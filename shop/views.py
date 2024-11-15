# shop/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm
from .models import Product, Order, Cart, CartItem, QuickOrder, Review, OrderReport
from .forms import OrderForm, QuickOrderForm, ReviewForm
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm, UserProfile, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .utils import generate_report
from django.http import HttpResponse
import csv
import os
from django.utils import timezone
from django.db.models import Sum
from telegram_bot.bot import send_order_notification
import asyncio


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            login(request, user)
            return redirect('product_list')  # Перенаправление на страницу каталога
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})

def product_list(request):
    # Отображение всех товаров
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

@login_required
def add_to_cart(request, product_id):
    # Получаем товар по ID
    product = get_object_or_404(Product, id=product_id)

    # Получаем или создаём корзину для текущего пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Проверяем, есть ли уже товар в корзине
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Если товар уже есть в корзине, увеличиваем его количество
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')  # Перенаправляем на страницу корзины

@login_required
def cart_view(request):
    user_profile = getattr(request.user, 'profile', None)

    # Проверка на заполненность профиля
    if user_profile and (not user_profile.phone or not user_profile.address):
        messages.warning(request, "Для оформления заказа, пожалуйста, заполните профиль.")
        return redirect('profile_edit')

    # Получаем корзину текущего пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()

    # Вычисление общей стоимости
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        if cart_items.exists():
            # Создаём объект QuickOrder только один раз
            quick_order = QuickOrder.objects.create(
                customer_name=request.user.get_full_name(),
                customer_email=request.user.email,
                customer_phone=user_profile.phone,
                delivery_address=user_profile.address,
                order_type='cart',
                user=request.user
            )

            # Добавляем каждый элемент корзины как отдельный Order в QuickOrder
            for item in cart_items:
                Order.objects.create(
                    quick_order=quick_order,
                    product=item.product,
                    quantity=item.quantity
                )

            cart.items.all().delete()  # Очистка корзины
            return redirect('order_success')
        else:
            messages.warning(request, "Ваша корзина пуста.")
            return redirect('cart')

    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def home(request):
    return render(request, 'shop/home.html')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_view')

@login_required
def account(request):
    return render(request, 'shop/account.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('account')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('product_list')

def quick_buy(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product  # Возможно, стоит убрать это, так как QuickOrder теперь не содержит отдельного продукта
            order.save()
            send_order_notification(order.id)
            return redirect('quick_order_success')  # Страница успешного оформления заказа
    else:
        form = QuickOrderForm()
    return render(request, 'shop/quick_buy.html', {'form': form, 'product': product})

def quick_order_success(request):
    return render(request, 'shop/quick_order_success.html')

def order_success(request):
    return render(request, 'shop/order_success.html')

@login_required
def profile_edit_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('cart')  # После сохранения перенаправляем обратно в корзину
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'shop/profile_edit.html', {'form': form})

def order_history(request):
    # Получаем заказы пользователя вместе с товарами
    orders = QuickOrder.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')

    # Отправляем заказы в шаблон
    return render(request, 'shop/order_history.html', {'orders': orders})

def reorder(request, order_id):
    original_order = get_object_or_404(QuickOrder, id=order_id)

    if request.method == 'POST':
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            # Создание нового заказа на основе оригинала
            new_order = form.save(commit=False)
            new_order.status = 'accepted'
            new_order.user = request.user
            new_order.save()  # Сохранение для получения ID заказа

            # Копирование товаров из оригинального заказа
            for item in original_order.items.all():
                Order.objects.create(
                    quick_order=new_order,
                    product=item.product,
                    quantity=item.quantity
                )

            # Отправка уведомления после добавления всех товаров
            asyncio.run(send_order_notification(new_order.id))
            return redirect('order_history')
    else:
        form = QuickOrderForm(initial={
            'customer_name': original_order.customer_name,
            'customer_email': original_order.customer_email,
            'customer_phone': original_order.customer_phone,
            'delivery_address': original_order.delivery_address,
            'delivery_datetime': original_order.created_at,
        })

    return render(request, 'shop/reorder_form.html', {'form': form})


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Ваш отзыв был добавлен.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'shop/add_review.html', {'form': form, 'product': product})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


def generate_report_view(request):
    report = generate_report()
    return HttpResponse(f"Отчёт за {report.date} успешно создан.")


def generate_report():
    today = timezone.now().date()

    # Подсчёт количества заказов и общей выручки за текущий день
    orders_today = QuickOrder.objects.filter(created_at__date=today)
    total_orders = orders_today.count()
    total_revenue = orders_today.aggregate(total=Sum('product__price'))['total'] or 0

    # Сохранение отчёта в базе данных
    report, created = OrderReport.objects.get_or_create(
        date=today,
        defaults={'total_orders': total_orders, 'total_revenue': total_revenue},
    )

    # Проверка существования директории "reports" и её создание при необходимости
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    # Экспорт отчёта в CSV-файл
    file_path = os.path.join(reports_dir, f'order_report_{today}.csv')
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Дата', 'Количество заказов', 'Общая выручка'])
        writer.writerow([today, total_orders, total_revenue])

    return report


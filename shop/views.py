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

    if user_profile and (not user_profile.phone or not user_profile.address):
        # Если не хватает телефона или адреса, перенаправляем на страницу профиля
        messages.warning(request, "Для оформления заказа, пожалуйста, заполните профиль.")
        return redirect('profile_edit')  # Укажите правильный URL для редактирования профиля
    # Получаем корзину текущего пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Получаем все товары в корзине
    cart_items = cart.items.all()

    if request.method == 'POST':
        # Создаём заказ для каждого товара в корзине
        for item in cart_items:
            QuickOrder.objects.create(
                product=item.product,
                customer_name=request.user.get_full_name(),
                customer_email=request.user.email,
                customer_phone=request.user.profile.phone,  # предполагаем, что у пользователя есть профиль с телефоном
                delivery_address=request.user.profile.address,  # предполагаем, что у пользователя есть профиль с адресом
                quantity=item.quantity,
                order_type='cart',
                user=request.user
            )

        # После создания заказов очищаем корзину
        cart.items.all().delete()

        # Перенаправляем пользователя на страницу подтверждения заказа
        return redirect('order_success')

    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'cart': cart})

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
            order.product = product
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
    # Получаем все заказы пользователя
    orders = QuickOrder.objects.filter(user=request.user).order_by('-created_at')

    # Отправляем заказы в шаблон
    return render(request, 'shop/order_history.html', {'orders': orders})


def reorder(request, order_id):
    original_order = get_object_or_404(QuickOrder, id=order_id)

    # Если запрос POST, то создаем новый заказ на основе формы
    if request.method == 'POST':
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            # Создаём новый заказ
            new_order = form.save(commit=False)
            new_order.product = original_order.product
            new_order.status = 'accepted'  # Статус по умолчанию
            new_order.user = request.user  # Привязываем заказ к текущему пользователю
            new_order.save()

            # Перенаправление в историю заказов
            return redirect('order_history')
    else:
        # Если запрос GET, передаем форму с уже предзаполненными данными
        form = QuickOrderForm(initial={
            'customer_name': original_order.customer_name,
            'customer_email': original_order.customer_email,
            'customer_phone': original_order.customer_phone,
            'delivery_address': original_order.delivery_address,
            'quantity': original_order.quantity,
            'delivery_datetime': original_order.created_at,  # Дата и время из старого заказа
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


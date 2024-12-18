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
import logging
from django.conf import settings


# Настроим логгер
logger = logging.getLogger('shop')



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
        # Обработка формы с уточнением данных
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            # Создаём объект QuickOrder только один раз
            quick_order = form.save(commit=False)
            quick_order.order_type = 'cart'  # Указываем, что это заказ из корзины
            quick_order.user = request.user
            quick_order.save()  # Сохраняем заказ, чтобы получить его ID

            # Добавляем каждый элемент из корзины как отдельный Order
            for item in cart_items:
                Order.objects.create(
                    quick_order=quick_order,
                    product=item.product,
                    quantity=item.quantity
                )

            # Отправка уведомления о заказе
            asyncio.run(send_order_notification(quick_order.id))

            # Очищаем корзину
            cart.items.all().delete()

            return redirect('order_success')
        else:
            messages.error(request, "Пожалуйста, заполните все поля корректно.")
    else:
        # Инициализируем форму с данными из профиля пользователя, если они есть
        form = QuickOrderForm(initial={
            'customer_name': request.user.get_full_name(),
            'customer_email': request.user.email,
            'customer_phone': user_profile.phone if user_profile else '',
            'delivery_address': user_profile.address if user_profile else '',
        })

    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'form': form})

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
            order.save()  # Сохраняем сам заказ сначала

            # Создаем связанный объект Order и связываем с заказом и продуктом
            Order.objects.create(quick_order=order, product=product, quantity=1)  # Можно задать количество, если нужно

            # Отправляем уведомление о новом заказе
            asyncio.run(send_order_notification(order.id))

            return redirect('quick_order_success')
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


def generate_report(report_param_id):
    # Получаем параметры отчёта
    parameter = ReportParameter.objects.get(id=report_param_id)

    # Считаем данные за указанный период
    orders = QuickOrder.objects.filter(
        created_at__range=[parameter.start_date, parameter.end_date]
    )
    total_orders = orders.count()
    total_bouquets = orders.aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Создаём объект отчёта
    report = Report.objects.create(
        parameter=parameter,
        total_orders=total_orders,
        total_bouquets=total_bouquets,
        total_revenue=total_revenue,
    )

    # Генерируем CSV-файл
    file_path = f"reports/report_{report.id}.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Параметр", "Количество заказов", "Количество букетов", "Общая выручка"])
        writer.writerow([parameter.name, total_orders, total_bouquets, total_revenue])

    # Привязываем файл к объекту отчёта
    with open(file_path, 'rb') as csvfile:
        report.file.save(f"report_{report.id}.csv", csvfile)

    return report


def generate_csv_report(start_date, end_date, report):
    """
    Генерация CSV-отчёта и сохранение данных в Report.
    """
    orders = QuickOrder.objects.filter(created_at__range=(start_date, end_date))
    total_orders = orders.count()
    total_bouquets = sum(item.quantity for order in orders for item in order.items.all())
    total_revenue = sum(order.total_price for order in orders)

    # Сохраняем данные в модель Report
    report.total_orders = total_orders
    report.total_bouquets = total_bouquets
    report.total_revenue = total_revenue
    report.save()

    # Генерация CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="report_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID заказа', 'Дата', 'Клиент', 'Общая сумма', 'Статус'])
    for order in orders:
        writer.writerow([order.id, order.created_at, order.customer_name, order.total_price, order.get_status_display()])

    # Генерация полного пути для сохранения файла
    file_name = f'report_{report.id}.csv'
    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', file_name)

    # Создание директории, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Сохраняем CSV в файл
    with open(file_path, 'w', newline='') as file:
        file.write(response.content.decode('utf-8'))

    # Сохраняем путь к файлу в модель Report
    report.file.name = os.path.join('reports', file_name)  # Только относительно MEDIA_ROOT
    report.save()


@login_required
def checkout(request):
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
        # Обработка формы с уточнением данных
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            # Создаём объект QuickOrder только один раз
            quick_order = form.save(commit=False)
            quick_order.order_type = 'cart'  # Указываем, что это заказ из корзины
            quick_order.user = request.user
            quick_order.save()  # Сохраняем заказ, чтобы получить его ID

            # Добавляем каждый элемент из корзины как отдельный Order
            for item in cart_items:
                Order.objects.create(
                    quick_order=quick_order,
                    product=item.product,
                    quantity=item.quantity
                )

            # Отправка уведомления о заказе
            asyncio.run(send_order_notification(quick_order.id))

            # Очищаем корзину
            cart.items.all().delete()

            return redirect('order_success')  # Перенаправление на страницу успеха
        else:
            messages.error(request, "Пожалуйста, заполните все поля корректно.")
    else:
        # Инициализируем форму с данными из профиля пользователя, если они есть
        form = QuickOrderForm(initial={
            'customer_name': request.user.get_full_name(),
            'customer_email': request.user.email,
            'customer_phone': user_profile.phone if user_profile else '',
            'delivery_address': user_profile.address if user_profile else '',
        })

    return render(request, 'shop/checkout.html', {'form': form, 'cart_items': cart_items, 'total_price': total_price})
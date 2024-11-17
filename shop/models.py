# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None


class Order(models.Model):
    quick_order = models.ForeignKey('QuickOrder', on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Товар {self.product.name} в заказе {self.quick_order.id}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


class QuickOrder(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят к работе'),
        ('in_progress', 'Находится в работе'),
        ('delivering', 'В доставке'),
        ('completed', 'Выполнен'),
    ]

    ORDER_TYPE_CHOICES = [
        ('quick', 'Быстрая покупка'),
        ('cart', 'Корзина'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='cart')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_name} ({self.get_status_display()})"

    @property
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.items.all())


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)  # Оценка от 1 до 5
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username} для {self.product.name} с оценкой {self.rating}"


class OrderReport(models.Model):
    date = models.DateField(default=timezone.now)
    total_orders = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Отчёт за {self.date}"


class ReportParameter(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название отчета")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.name


class Report(models.Model):
    parameter = models.ForeignKey(ReportParameter, on_delete=models.CASCADE, related_name="reports")
    file = models.FileField(upload_to='reports/', verbose_name="Файл отчета", blank=True, null=True)
    total_orders = models.PositiveIntegerField(verbose_name="Общее количество заказов", default=0)
    total_bouquets = models.PositiveIntegerField(verbose_name="Количество букетов", default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая выручка", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отчет: {self.parameter.name} ({self.created_at})"

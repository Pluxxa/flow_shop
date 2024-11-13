from django.contrib import admin
from .models import Product, Cart, CartItem, Order, QuickOrder  # Импорт модели Product


# Регистрируем модель Product в админке
admin.site.register(Product)


# Регистрация модели QuickOrder для отображения в админке
@admin.register(QuickOrder)
class QuickOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'customer_name', 'customer_email', 'quantity', 'created_at', 'status', 'order_type', 'user')
    list_filter = ('status', 'order_type')
    search_fields = ('customer_name', 'customer_email')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request, obj=None):
        return False  # Отключаем добавление через админ-панель

    def has_delete_permission(self, request, obj=None):
        return True  # Включаем возможность удаления
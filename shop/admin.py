from django.contrib import admin
from .models import Product, Cart, CartItem, Order, QuickOrder

# Регистрируем модель Product в админке
admin.site.register(Product)

# Определяем Inline для отображения товаров в заказе
class OrderInline(admin.TabularInline):
    model = Order
    extra = 0  # Убираем дополнительные пустые строки для добавления новых товаров
    readonly_fields = ('product', 'quantity', 'created_at')
    can_delete = False  # Отключаем возможность удаления товаров из QuickOrder через админку

# Регистрация модели QuickOrder для отображения в админке
@admin.register(QuickOrder)
class QuickOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'created_at', 'status', 'order_type', 'user')
    list_filter = ('status', 'order_type')
    search_fields = ('customer_name', 'customer_email')
    readonly_fields = ('created_at', 'total_price')  # Отображаем общую цену заказа

    inlines = [OrderInline]  # Добавляем Inline для отображения товаров в QuickOrder

    def has_add_permission(self, request, obj=None):
        return False  # Отключаем добавление через админ-панель

    def has_delete_permission(self, request, obj=None):
        return True  # Включаем возможность удаления

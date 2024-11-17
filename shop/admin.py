from django.contrib import admin
from .models import Product, Cart, CartItem, Order, QuickOrder, ReportParameter, Report
from .views import generate_report

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


@admin.register(ReportParameter)
class ReportParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name',)
    actions = ['generate_report']

    def generate_report(self, request, queryset):
        for param in queryset:
            generate_report(param)
        self.message_user(request, f"Отчёты для {queryset.count()} параметров успешно созданы.")

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('parameter', 'total_orders', 'total_bouquets', 'total_revenue', 'created_at')
    readonly_fields = ('file', 'total_orders', 'total_bouquets', 'total_revenue')
    list_filter = ('created_at',)
from django.contrib import admin
from .models import Product, Cart, CartItem, Order, QuickOrder, Report, ReportParameter
from .views import generate_report
import logging
from telegram_bot.bot import send_report_to_telegram
from django.utils.html import format_html
from django.urls import path
from .views import generate_csv_report
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django import forms

# Настроим логгер
logger = logging.getLogger(__name__)


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


class ReportForm(forms.Form):
    """
    Форма для выбора диапазона дат.
    """
    start_date = forms.DateField(label="Начальная дата", widget=forms.SelectDateWidget)
    end_date = forms.DateField(label="Конечная дата", widget=forms.SelectDateWidget)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('parameter', 'created_at', 'total_orders', 'total_bouquets', 'total_revenue', 'file')
    readonly_fields = ('total_orders', 'total_bouquets', 'total_revenue', 'file')

    def get_urls(self):
        """
        Подключаем кастомный URL для формы создания отчёта и отправки отчёта в Telegram.
        """
        urls = super().get_urls()
        custom_urls = [
            path('add/', self.admin_site.admin_view(self.create_report_view), name='create-report'),
            path('send_report/<int:report_id>/', self.admin_site.admin_view(self.send_report_view), name='send-report'),
        ]
        return custom_urls + urls

    def create_report_view(self, request):
        """
        Кастомный обработчик для создания отчёта.
        """
        if request.method == 'POST':
            form = ReportForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']

                # Генерация отчёта
                report = Report.objects.create(parameter=f"Отчёт с {start_date} по {end_date}")
                generate_csv_report(start_date, end_date, report)  # Передаем объект Report в функцию

                self.message_user(request, "Отчёт успешно создан!")
                return redirect('admin:shop_report_changelist')
        else:
            form = ReportForm()

        # Рендерим страницу с формой
        return render(request, 'admin/report_form.html', {'form': form})

    def send_report_view(self, request, report_id):
        """
        Кастомный обработчик для отправки отчёта в Telegram.
        """
        report = Report.objects.get(id=report_id)

        # Путь к файлу отчёта
        report_file_path = report.file.path

        # Отправка отчёта в Telegram
        send_report_to_telegram(report_file_path)

        # Уведомление в админке
        self.message_user(request, "Отчёт отправлен в Telegram.")
        return redirect('admin:shop_report_changelist')

    def get_actions(self, request):
        """
        Мы добавляем действие отправки отчёта в Telegram на страницу списка отчетов.
        """
        actions = super().get_actions(request)

        # Добавляем наше действие
        actions['send_report'] = (
            self.send_report_action,
            'send_report',
            "Отправить выбранные отчёты в Telegram"
        )
        return actions

    def send_report_action(self, request, queryset):
        """
        Действие для отправки выбранных отчетов в Telegram.
        Принимает три аргумента: self, request, queryset
        """
        for report in queryset:
            # Путь к файлу отчёта
            report_file_path = report.file.path

            # Отправка отчёта в Telegram
            send_report_to_telegram(report_file_path)

        self.message_user(request, "Отчёты отправлены в Telegram.")
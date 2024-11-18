from django.contrib import admin
from .models import Product, Cart, CartItem, Order, QuickOrder, Report, ReportParameter
from .views import generate_report
import logging
from telegram_bot.telegram_sync import send_report_to_telegram_async, send_report_in_thread
from telegram_bot.bot import send_report_to_telegram
from django.utils.html import format_html
from django.urls import path
from .views import generate_csv_report
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django import forms
import asyncio
import threading

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
    list_display = ('parameter', 'created_at', 'total_orders', 'total_bouquets', 'total_revenue', 'file', 'send_report_button')
    readonly_fields = ('total_orders', 'total_bouquets', 'total_revenue', 'file')

    def send_report_button(self, obj):
        """
        Добавляем кнопку для отправки отчёта в Telegram.
        """
        return format_html(
            '<a href="/admin/shop/report/send_report/{}/" class="button" style="background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">Отправить в Telegram</a>',
            obj.id
        )
    send_report_button.allow_tags = True
    send_report_button.short_description = 'Действия'

    def get_urls(self):
        """
        Подключаем кастомные URL для формы создания отчёта и отправки отчёта в Telegram.
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
                try:
                    report = Report.objects.create(parameter=f"Отчёт с {start_date} по {end_date}")
                    generate_csv_report(start_date, end_date, report)
                    self.message_user(request, "Отчёт успешно создан!")
                    return redirect('admin:shop_report_changelist')
                except Exception as e:
                    self.message_user(request, f"Ошибка при создании отчёта: {e}", level='error')
                    logger.error(f"Ошибка при создании отчёта: {e}")
        else:
            form = ReportForm()

        return render(request, 'admin/report_form.html', {'form': form})

    def send_report_view(self, request, report_id):
        """
        Синхронный обработчик для отправки отчёта в Telegram.
        """
        report = Report.objects.get(id=report_id)
        try:
            report_file_path = report.file.path
            # Отправляем отчёт в отдельном потоке
            threading.Thread(target=send_report_in_thread, args=(report_file_path,)).start()
            self.message_user(request, "Отчёт отправлен в Telegram.")
        except Exception as e:
            self.message_user(request, f"Ошибка при отправке отчёта в Telegram: {e}", level='error')
            logger.error(f"Ошибка при отправке отчёта в Telegram: {e}")
        return redirect('admin:shop_report_changelist')
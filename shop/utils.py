# shop/utils.py
import csv
from django.utils import timezone
from django.db.models import Sum
from .models import QuickOrder, OrderReport


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

    # Экспорт отчёта в CSV-файл
    with open(f'reports/order_report_{today}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Дата', 'Количество заказов', 'Общая выручка'])
        writer.writerow([today, total_orders, total_revenue])

    return report

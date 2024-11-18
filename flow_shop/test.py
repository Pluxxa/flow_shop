import csv
import os
from django.conf import settings
from .models import QuickOrder

def generate_csv_report(start_date, end_date, report):
    """
    Генерация CSV-отчёта и сохранение данных в Report.
    """
    # Получаем заказы за указанный период
    orders = QuickOrder.objects.filter(created_at__range=(start_date, end_date))
    total_orders = orders.count()
    total_bouquets = sum(item.quantity for order in orders for item in order.items.all())
    total_revenue = sum(order.total_price for order in orders)

    # Сохраняем данные в модель Report
    report.total_orders = total_orders
    report.total_bouquets = total_bouquets
    report.total_revenue = total_revenue
    report.save()

    # Генерация имени и пути для файла
    file_name = f'report_{report.id}.csv'
    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', file_name)

    # Создание директории, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Генерация CSV и сохранение в файл с кодировкой UTF-8
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID заказа', 'Дата', 'Клиент', 'Общая сумма', 'Статус'])
        for order in orders:
            writer.writerow([order.id, order.created_at, order.customer_name, order.total_price, order.get_status_display()])

    # Привязываем файл к объекту отчёта
    report.file.name = os.path.join('reports', file_name)
    report.save()

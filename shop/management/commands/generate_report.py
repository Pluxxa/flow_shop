import io
import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
import telegram
from shop.models import QuickOrder
from django.conf import settings
import asyncio

bot = telegram.Bot(token=settings.TOKEN)


class Command(BaseCommand):
    help = 'Генерация отчета по заказам за указанный период и отправка его в Telegram'

    def add_arguments(self, parser):
        parser.add_argument('start_date', type=str, help='Дата начала периода в формате YYYY-MM-DD')
        parser.add_argument('end_date', type=str, help='Дата конца периода в формате YYYY-MM-DD')

    def handle(self, *args, **options):
        start_date = timezone.datetime.strptime(options['start_date'], '%Y-%m-%d')
        end_date = timezone.datetime.strptime(options['end_date'], '%Y-%m-%d') + timezone.timedelta(days=1)

        orders = QuickOrder.objects.filter(created_at__gte=start_date, created_at__lt=end_date)

        # Формирование данных для отчета
        report_data = [["ID заказа", "Имя клиента", "Дата заказа", "Сумма заказа"]]
        for order in orders:
            report_data.append([
                order.id,
                order.customer_name,
                order.created_at,
                order.total_price,
            ])

        # Сохранение отчета в CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(report_data)
        output.seek(0)

        # Отправка файла через Telegram
        async def send_report():
            bot = telegram.Bot(token=settings.TOKEN)  # Замените на ваш токен
            chat_id = settings.TELEGRAM_CHAT_ID  # Замените на ваш chat_id
            await bot.send_document(chat_id=chat_id, document=output, filename="report.csv")

        asyncio.run(send_report())


import telegram
import logging
from django.template.loader import render_to_string
from django.conf import settings
from shop.models import QuickOrder, Order  # Добавить импорт модели Order
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
import asyncio


# Инициализация бота с токеном
bot = telegram.Bot(token=settings.TOKEN)

logger = logging.getLogger(__name__)

async def send_message_to_telegram(message, photo=None):
    """Функция отправки сообщений и фото в Telegram."""
    async with telegram.Bot(token=settings.TOKEN) as bot:
        try:
            await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
            if photo:
                with open(photo, 'rb') as photo_file:
                    await bot.send_photo(chat_id=settings.TELEGRAM_CHAT_ID, photo=photo_file)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")

@sync_to_async
def render_order_template(order):
    """Рендеринг шаблона для уведомления о заказе."""
    return render_to_string('shop/order_notification.txt', {'order': order})

# Оптимизированная функция для получения заказа с его товарами
@sync_to_async
def get_order_with_items(order_id):
    """Получаем заказ с товарами и их изображениями."""
    order = QuickOrder.objects.prefetch_related(
        Prefetch('items', queryset=Order.objects.select_related('product'))
    ).get(id=order_id)

    # Диагностический вывод, чтобы проверить связанные элементы
    related_items = order.items.all()
    print(f"Связанные позиции для заказа #{order.id}: {[str(item) for item in related_items]}")  # Вывод всех элементов

    return order

async def send_order_notification(order_id):
    """Функция для отправки уведомления о новом заказе с деталями."""
    try:
        # Получение заказа с позициями
        order = await get_order_with_items(order_id)
        items = order.items.all()

        # Генерация сообщения для Telegram
        message = await render_order_template(order)
        await send_message_to_telegram(message)

        # Отправка фото каждого продукта
        for item in items:
            product = item.product
            if product.image:
                await send_message_to_telegram(
                    f"Продукт: {product.name}",
                    photo=product.image.path
                )
                await asyncio.sleep(1)
    except QuickOrder.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")


async def send_order_status_update(order_id):
    """Функция для отправки уведомления об обновлении статуса заказа."""
    try:
        order = await get_order_with_items(order_id)
        status_message = f"Заказ #{order.id} обновлен: статус - {order.get_status_display()}"
        await send_message_to_telegram(status_message)
    except QuickOrder.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")


def send_report_to_telegram(file_path):
    bot_token = "ВАШ_ТОКЕН_БОТА"
    chat_id = "ВАШ_CHAT_ID"
    bot = telegram.Bot(token=bot_token)

    with open(file_path, 'rb') as file:
        bot.send_document(chat_id=chat_id, document=file)

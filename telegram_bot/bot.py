# bot.py
import telegram
from django.template.loader import render_to_string
from django.conf import settings
from shop.models import QuickOrder
from asgiref.sync import sync_to_async  # Импорт для sync_to_async

# Инициализация бота с токеном
bot = telegram.Bot(token=settings.TOKEN)

async def send_message_to_telegram(message, photo=None):
    """Функция отправки сообщений и фото в Telegram."""
    try:
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
        if photo:
            await bot.send_photo(chat_id=settings.TELEGRAM_CHAT_ID, photo=photo)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

@sync_to_async
def get_order_from_db(order_id):
    """Получаем заказ из базы данных (обертка для синхронного запроса)."""
    return QuickOrder.objects.get(id=order_id)

@sync_to_async
def render_order_template(order):
    """Рендеринг шаблона для уведомления о заказе (синхронная операция)."""
    return render_to_string('shop/order_notification.txt', {'order': order})

async def send_order_notification(order_id):
    """Функция для отправки уведомления о новом заказе."""
    try:
        order = await get_order_from_db(order_id)
        message = await render_order_template(order)
        await send_message_to_telegram(message, photo=order.product.image.path if order.product.image else None)
    except QuickOrder.DoesNotExist:
        print(f"Order with ID {order_id} not found.")

async def send_order_status_update(order_id):
    """Функция для отправки уведомления об обновлении статуса заказа."""
    try:
        order = await get_order_from_db(order_id)
        status_message = f"Заказ #{order.id} обновлен: статус - {order.status}"
        await send_message_to_telegram(status_message)
    except QuickOrder.DoesNotExist:
        print(f"Order with ID {order_id} not found.")

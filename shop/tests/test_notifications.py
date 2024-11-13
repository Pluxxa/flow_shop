import pytest
from unittest.mock import patch
from shop.models import Product, QuickOrder
from telegram_bot.bot import send_order_notification

@pytest.mark.asyncio
@patch('telegram_bot.bot.send_order_notification')  # Патчим функцию в файле bot.py
async def test_telegram_notification_sent(mock_send_notification):
    # Создаем продукт для теста
    product = Product.objects.create(
        name="Test Flower",
        description="A beautiful flower",
        price=100
    )

    # Создаем заказ QuickOrder с этим продуктом
    quick_order = QuickOrder.objects.create(
        product=product,
        customer_name="Test User",
        customer_email="testuser@example.com",
        customer_phone="123456789",
        delivery_address="123 Test St",
        quantity=1
    )

    # Выполняем асинхронную функцию
    await send_order_notification(quick_order.id)

    # Проверяем, что уведомление было отправлено
    mock_send_notification.assert_called_once_with(quick_order.id)

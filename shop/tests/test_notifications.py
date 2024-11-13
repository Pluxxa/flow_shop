from unittest.mock import patch, MagicMock
from django.test import TestCase
from shop.models import Product, QuickOrder
from telegram_bot.bot import send_order_notification


class TestTelegramNotification(TestCase):

    @patch('telegram_bot.bot.send_message_to_telegram')  # Патчим send_message_to_telegram
    @patch('telegram_bot.bot.get_order_from_db')
    @patch('telegram_bot.bot.render_order_template')
    def test_telegram_notification_sent(self, mock_render, mock_get_order, mock_send_message):
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

        # Мокаем вызовы
        mock_get_order.return_value = quick_order
        mock_render.return_value = "Order message content"  # Строка с текстом сообщения

        # Мокаем отправку сообщения в Telegram
        mock_send_message.return_value = MagicMock()

        # Используем async_to_sync для вызова асинхронной функции
        from asgiref.sync import async_to_sync
        async_to_sync(send_order_notification)(quick_order.id)

        # Проверяем, что send_message_to_telegram была вызвана только один раз
        self.assertEqual(mock_send_message.call_count, 1)

        # Проверяем, что в первом вызове были переданы правильные аргументы
        call_args = mock_send_message.call_args[0]
        self.assertEqual(call_args[0], "Order message content")  # Проверка текста сообщения
        self.assertEqual(call_args[1], None)  # Проверка, что фото не передается

        # Дополнительный вывод вызова
        print("send_message_to_telegram calls:", mock_send_message.call_args_list)

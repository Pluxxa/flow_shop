# telegram_sync.py

import telegram
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def send_message_to_telegram_sync(message, photo=None):
    """Синхронная функция отправки сообщений и фото в Telegram."""
    try:
        bot = telegram.Bot(token=settings.TOKEN)
        bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
        if photo:
            with open(photo, 'rb') as photo_file:
                bot.send_photo(chat_id=settings.TELEGRAM_CHAT_ID, photo=photo_file)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


def send_report_to_telegram_sync(file_path):
    """
    Синхронная отправка отчёта в Telegram.
    """
    bot_token = settings.TOKEN  # Токен бота
    chat_id = settings.TELEGRAM_CHAT_ID  # Идентификатор чата

    try:
        bot = telegram.Bot(token=bot_token)

        # Получаем информацию о боте синхронно
        bot_info = bot.get_me()
        print(f"Информация о боте: {bot_info}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Синхронно отправляем отчёт в Telegram
        with open(file_path, 'rb') as file:
            print(f"Отправляем файл: {file_path}")
            bot.send_document(chat_id=chat_id, document=file, filename="report.csv")

        print("Отчёт успешно отправлен в Telegram.")
    except Exception as e:
        print(f"Ошибка при отправке отчёта в Telegram: {e}")
        logger.error(f"Ошибка при отправке отчёта в Telegram: {e}")

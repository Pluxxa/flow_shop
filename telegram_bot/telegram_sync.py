import telegram
import logging
import os
from django.conf import settings
import asyncio
import threading

logger = logging.getLogger(__name__)

# Асинхронная функция отправки сообщений и файлов в Telegram
async def send_message_to_telegram_1(message, file=None):
    """Асинхронная функция отправки сообщений и файлов в Telegram."""
    async with telegram.Bot(token=settings.TOKEN) as bot:
        try:
            # Отправка текстового сообщения
            await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)

            # Если передан файл, отправляем его
            if file:
                with open(file, 'rb') as file_data:
                    await bot.send_document(chat_id=settings.TELEGRAM_CHAT_ID, document=file_data, filename="report.csv")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения или файла: {e}")

# Функция для отправки отчета в Telegram
async def send_report_to_telegram_async(file_path):
    """
    Асинхронная отправка отчёта в Telegram.
    """
    bot_token = settings.TOKEN  # Токен бота
    chat_id = settings.TELEGRAM_CHAT_ID  # Идентификатор чата

    try:
        bot = telegram.Bot(token=bot_token)

        # Получаем информацию о боте асинхронно
        bot_info = await bot.get_me()
        print(f"Информация о боте: {bot_info}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Отправка файла в Telegram
        with open(file_path, 'rb') as file:
            print(f"Отправляем файл: {file_path}")
            await bot.send_document(chat_id=chat_id, document=file, filename="report.csv")

        print("Отчёт успешно отправлен в Telegram.")
    except Exception as e:
        print(f"Ошибка при отправке отчёта в Telegram: {e}")
        logger.error(f"Ошибка при отправке отчёта в Telegram: {e}")

# Функция для выполнения асинхронной задачи в потоке
def send_report_in_thread(file_path):
    loop = asyncio.new_event_loop()  # Создаём новый event loop для потока
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_report_to_telegram_async(file_path))

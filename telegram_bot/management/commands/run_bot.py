# telegram_bot/management/commands/run_bot.py

from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from django.conf import settings
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Определите обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш бот для уведомлений.")

class Command(BaseCommand):
    help = 'Запускает Telegram-бота'

    def handle(self, *args, **kwargs):
        # Инициализация приложения для бота
        application = Application.builder().token(settings.TOKEN).build()

        # Обработчик команды /start
        application.add_handler(CommandHandler("start", start))

        # Запуск бота
        application.run_polling()
        self.stdout.write("Бот запущен и ожидает сообщений.")

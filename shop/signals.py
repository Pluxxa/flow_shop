import asyncio
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, QuickOrder
from telegram_bot.bot import send_order_notification, send_order_status_update
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

# Вспомогательная функция для запуска асинхронных функций
def run_async(func):
    """Запуск асинхронной функции в отдельном цикле событий."""
    loop = asyncio.new_event_loop()  # Создаем новый цикл событий
    asyncio.set_event_loop(loop)  # Устанавливаем его как текущий
    loop.run_until_complete(func)  # Запускаем асинхронную функцию до завершения

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля пользователя при его создании."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля пользователя при его изменении."""
    instance.profile.save()

# Обработчик сигнала для нового заказа
@receiver(post_save, sender=QuickOrder)
def order_created(sender, instance, created, **kwargs):
    """Обработчик нового заказа для отправки уведомления."""
    if created:
        # Ждем, пока связанные элементы заказа не будут полностью доступны
        if instance.items.exists():
            async_to_sync(send_order_notification)(instance.id)
        else:
            # Отложенная задача для повторной попытки отправки уведомления
            async_to_sync(asyncio.sleep)(0.5)  # Задержка 0.5 секунды
            if instance.items.exists():
                async_to_sync(send_order_notification)(instance.id)

# Обработчик сигнала для обновления статуса заказа
@receiver(pre_save, sender=QuickOrder)
def order_status_updated(sender, instance, **kwargs):
    """Обработчик изменения статуса заказа для отправки обновления."""
    if instance.pk:
        old_instance = QuickOrder.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            # Асинхронный вызов для обновления статуса заказа
            run_async(send_order_status_update(instance.id))

# Функция для получения заказа, обернутая в sync_to_async
@sync_to_async
def get_order(order_id):
    """Асинхронная обертка для получения заказа из базы данных."""
    return QuickOrder.objects.get(id=order_id)

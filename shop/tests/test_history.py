from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import Product, QuickOrder
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from shop.signals import order_created


class OrderHistoryTestCase(TestCase):
    def setUp(self):
        # Отключаем сигнал order_created, чтобы он не мешал тестированию
        post_save.disconnect(order_created, sender=QuickOrder)

        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='Pluxa11', password='password')

        # Создаем тестовый продукт
        self.product = Product.objects.create(
            name="Розы",
            description="Тестовое описание",
            price=500,
            image=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg')
        )

        # Создаем тестовый QuickOrder, связанный с пользователем
        self.order = QuickOrder.objects.create(
            user=self.user,
            product=self.product,
            customer_name=self.user.username,
            customer_email="test@example.com",
            customer_phone="1234567890",
            delivery_address="Test Address",
            quantity=1,
            status='accepted',
            order_type='cart'
        )

    def tearDown(self):
        # Восстанавливаем сигнал после тестирования
        post_save.connect(order_created, sender=QuickOrder)

    def test_order_history_access(self):
        # Входим под тестовым пользователем
        self.client.login(username='Pluxa11', password='password')

        # Открываем страницу истории заказов
        response = self.client.get(reverse('order_history'))

        # Проверяем, что страница загружается успешно
        self.assertEqual(response.status_code, 200)

        # Проверяем, что данные заказа присутствуют в ответе
        self.assertContains(response, 'История заказов')
        self.assertContains(response, self.product.name)  # Проверка имени продукта
        self.assertContains(response, 'Повторить заказ')  # Ссылка на повторный заказ

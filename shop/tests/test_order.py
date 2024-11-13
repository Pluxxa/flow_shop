from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import Product, Order

class OrderPlacementTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.product = Product.objects.create(name='Rose Bouquet', price=50)

    def test_order_creation(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('quick_buy', args=[self.product.id]), {  # Используем существующий URL
            'quantity': 2,
            'delivery_address': '123 Flower St.'
        })
        self.assertEqual(response.status_code, 200)  # Redirect after successful order
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_price, 100)  # 2 * 50

from django.test import TestCase
from django.urls import reverse
from shop.models import Product
from django.core.files.uploadedfile import SimpleUploadedFile


class ProductCatalogTestCase(TestCase):
    def setUp(self):
        product = Product.objects.create(
            name="Розы",
            description="Тестовое описание",
            price=500,
            image=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg')
        )

    def test_catalog_page_loads(self):
        response = self.client.get(reverse('product_list'))  # Исправлено на 'product_list'
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Розы')

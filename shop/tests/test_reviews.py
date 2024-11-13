from django.test import TestCase
from django.urls import reverse
from shop.models import Product, Review
from django.contrib.auth.models import User

class ReviewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.product = Product.objects.create(name='Rose Bouquet', price=50)

    def test_review_submission(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('add_review', args=[self.product.id]), {  # Указываем идентификатор продукта
            'rating': 5,
            'comment': 'Beautiful bouquet!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after posting review
        review = Review.objects.get(product=self.product)
        self.assertEqual(review.rating, 5)

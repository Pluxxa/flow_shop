from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class UserRegistrationTestCase(TestCase):
    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password1': 'strong_password',
            'password2': 'strong_password'
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_login(self):
        User.objects.create_user(username='testuser', password='testpass')
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertTrue(response.wsgi_request.user.is_authenticated)

# shop/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, QuickOrder, UserProfile, Review
from django.utils import timezone


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'delivery_address']


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают.")
        return password_confirm


class QuickOrderForm(forms.ModelForm):
    # Новые поля для уточнения доставки
    delivery_datetime = forms.DateTimeField(
        initial=timezone.now,  # Текущее время по умолчанию
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Дата и время доставки'
    )

    delivery_address = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Адрес доставки'
    )

    class Meta:
        model = QuickOrder
        fields = ['customer_name', 'customer_email', 'customer_phone', 'delivery_address', 'quantity', 'delivery_datetime']
        labels = {
            'customer_name': 'Имя',
            'customer_email': 'Электронная почта',
            'customer_phone': 'Телефон',
            'delivery_address': 'Адрес доставки',
            'quantity': 'Количество',
            'delivery_datetime': 'Дата и время доставки',
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']
        labels = {
            'phone': 'Телефон',
            'address': 'Адрес',
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        labels = {
            'rating': 'Оценка',
            'text': 'Отзыв',
        }
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
        }


# shop/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('catalog/', views.product_list, name='product_list'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('order_success/', views.order_success, name='order_success'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('account/', views.account, name='account'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quick_buy/<int:product_id>/', views.quick_buy, name='quick_buy'),
    path('quick_order_success/', views.quick_order_success, name='quick_order_success'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/orders/', views.order_history, name='order_history'),
    path('reorder/<int:order_id>/', views.reorder, name='reorder'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),
    path('generate_report/', views.generate_report_view, name='generate_report'),
    path('checkout/', views.checkout, name='checkout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

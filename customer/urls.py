from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('contact/', views.contact, name='contact'),
    path('products/', views.products, name='products'),
    path('product/', views.product_details, name='product_details'),
    path('category/', views.category_products, name='category_products'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('order-details/', views.order_details_view, name='order_details'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('terms-and-conditions/', views.terms_conditions_view, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]

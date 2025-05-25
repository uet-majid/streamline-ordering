from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    

    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('quick-add-to-cart/<int:product_id>/', views.quick_add_to_cart, name='quick_add_to_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/delete/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('create-stripe-session/', views.create_stripe_session, name='create_stripe_session'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),

    path('contact/', views.contact, name='contact'),

    path('products/', views.products, name='products'),
    path('product/<int:product_id>/', views.product_details, name='product_details'),

    path('category/<int:category_id>/', views.category_products, name='category_products'),

    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),

    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('order-details/<int:order_id>/', views.order_details_view, name='order_details_customer'),
    path('cancel-order/<int:order_id>/', views.cancel_order_view, name='cancel_order_customer'),
    path('order-via-whatsapp/', views.get_whatsapp_link, name='order_via_whatsapp'),

    path('about/', views.about, name='about'),
    path('terms-and-conditions/', views.terms_conditions_view, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),

    path('search/', views.search_results, name='search_results'),
]

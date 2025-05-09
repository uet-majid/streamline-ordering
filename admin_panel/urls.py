from django.urls import path
from . import views

# app_name = 'admin_panel'  # Namespace for your admin panel

urlpatterns = [
    path('', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_home, name='dashboard'),
    
    path('categories/', views.categories, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/', views.edit_category, name='edit_category'),
    
    path('products/', views.products, name='admin-products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/', views.edit_product, name='edit_product'),
    
    path('customers/', views.customers, name='customers'),
    
    path('contact-messages/', views.contact_messages, name='contact_messages'),
    path('contact-messages/<int:message_id>/', views.message_details, name='message_details'),
    
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_details, name='order_details'),
    
    path('reports', views.reports, name='reports'),
]
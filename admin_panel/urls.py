from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='admin_login'),
    path('staff/add/', views.add_staff, name='add_staff'),
    path('staff/view/', views.view_staff, name='view_staff'),
    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('staff/change-password/', views.staff_change_password, name='staff_change_password'),
    path('dashboard/', views.admin_home, name='dashboard'),
    
    path('categories/', views.categories, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
    path('products/', views.products, name='admin-products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    
    path('customers/', views.customers, name='customers'),
    
    path('contact-messages/', views.contact_messages, name='contact_messages'),
    path('contact-messages/<int:message_id>/', views.message_details, name='message_details'),
    
    path('orders/', views.orders, name='orders'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/', views.order_details, name='order_details'),
    path('orders/delivered/<int:order_id>/', views.mark_order_delivered, name='mark_order_delivered'),
    path('orders/cancelled/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('orders/invoice/<int:order_id>/', views.print_invoice, name='print_invoice'),
    path('orders/download_receipt/<int:order_id>/', views.download_receipt_pdf, name='download_receipt'),
    path('orders/<int:order_id>/resend-whatsapp/', views.resend_whatsapp, name='resend_whatsapp'),
    
    path('reports', views.reports, name='reports'),
    path('reports/download-pdf/', views.download_report_pdf, name='download_report_pdf'),

    path('logout/', views.admin_logout, name='admin_logout'),
]
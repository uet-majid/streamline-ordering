from django.shortcuts import render

def admin_login(request):
    return render(request, 'admin_panel/login.html')

def admin_home(request):
    return render(request, 'admin_panel/dashboard.html')

def add_category(request):
    return render(request, 'admin_panel/add_category.html')

def categories(request):
    return render(request, 'admin_panel/categories.html')

def edit_category(request):
    return render(request, 'admin_panel/edit_category.html')

def add_product(request):
    return render(request, 'admin_panel/add_product.html')

def products(request):
    return render(request, 'admin_panel/products.html')

def edit_product(request):
    return render(request, 'admin_panel/edit_product.html')

def customers(request):
    return render(request, 'admin_panel/customers.html')

def contact_messages(request):
    return render(request, 'admin_panel/contact_messages.html')

def message_details(request, message_id):
    # Dummy data - replace with actual database query later
    context = {
        'message_id': message_id,
        # In a real implementation, we would get the message from database:
    }
    return render(request, 'admin_panel/message_details.html', context)

def orders(request):
    return render(request, 'admin_panel/orders.html')

def order_details(request, order_id):
    # Dummy data - replace with actual database query later
    context = {
        'order_id': order_id,
        # In a real implementation, we would get the order from database:
        # 'order': get_object_or_404(Order, id=order_id)
        # 'order_items': OrderItem.objects.filter(order_id=order_id)
    }
    return render(request, 'admin_panel/order_details.html', context)

def reports(request):
    return render(request, 'admin_panel/reports.html')
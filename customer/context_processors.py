from admin_panel.models import Category
from customer.models import Cart

def header_categories(request):
    return {
        'header_categories': Category.objects.filter(is_active=True)
    }

def cart_count(request):
    count = 0
    customer_id = request.session.get('customer_id')
    if customer_id:
        count = Cart.objects.filter(customer_id=customer_id).count()
    return {'cart_count': count}
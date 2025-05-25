from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Order, OrderItem, AdminUser
from customer.models import Customer, ContactMessage
from django.contrib import messages
import json
from django.conf import settings
from decimal import Decimal
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from io import BytesIO
from django.contrib.auth.hashers import check_password, make_password
from .decorators import admin_login_required, superadmin_required
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import phonenumbers
import urllib.parse
from django.db.models import Prefetch

def admin_login(request):
    if request.session.get('admin_id'):
        return redirect('dashboard') 
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = AdminUser.objects.get(email=email, is_active=True)
        except AdminUser.DoesNotExist:
            messages.error(request, "Your account is deactivated.")
            return redirect('admin_login')

        if check_password(password, user.password):
            user.last_login = timezone.now()
            user.save()
            # Save user in session
            request.session['admin_id'] = user.id
            request.session['admin_role'] = user.role
            request.session['admin_name'] = user.name
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password")
            return redirect('admin_login')

    return render(request, 'admin_panel/login.html')

@superadmin_required
def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        form_data = request.POST.dict()

        if AdminUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        elif AdminUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            AdminUser.objects.create(
                username=username,
                name=name,
                email=email,
                password=make_password(password),
                role=role
            )
            messages.success(request, 'Staff added successfully.')
            return redirect('view_staff')

        return render(request, 'admin_panel/add_staff.html', {'form_data': form_data})

    return render(request, 'admin_panel/add_staff.html', {'form_data': {}})

@superadmin_required
def view_staff(request):
    staff_users = AdminUser.objects.all().order_by('-id')
    return render(request, 'admin_panel/view_staff.html', {'staff_users': staff_users})

@superadmin_required
def edit_staff(request, staff_id):
    staff = get_object_or_404(AdminUser, id=staff_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        if not name or not email or not role:
            messages.error(request, 'All fields are required.')
            return redirect('edit_staff', staff_id=staff_id)
        
        if AdminUser.objects.filter(email=email).exclude(id=staff_id).exists():
            messages.error(request, 'Email already exists.')
            return redirect('edit_staff', staff_id=staff_id)

        staff.name = name
        staff.email = email
        staff.role = role
        staff.is_active = is_active
        staff.save()

        messages.success(request, 'Staff member updated successfully.')
        return redirect('view_staff')

    return render(request, 'admin_panel/edit_staff.html', {'staff': staff})

@superadmin_required
def delete_staff(request, staff_id):
    staff = get_object_or_404(AdminUser, id=staff_id)
    staff.delete()
    messages.success(request, 'Staff member deleted successfully.')
    return redirect('view_staff')

@admin_login_required
def staff_change_password(request):
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    user = AdminUser.objects.get(id=request.session['admin_id'])

    if request.method == 'POST':
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if not check_password(current, user.password):
            messages.error(request, 'Current password is incorrect.')
        elif new != confirm:
            messages.error(request, 'New passwords do not match.')
        elif len(new) < 6:
            messages.error(request, 'New password must be at least 6 characters.')
        else:
            user.password = make_password(new)
            user.save()
            messages.success(request, 'Password changed successfully.')
            return redirect('staff_change_password')

    return render(request, 'admin_panel/change_password.html', {'user': user})

@admin_login_required
def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

@admin_login_required
def admin_home(request):
    today = timezone.now().date()

    # Orders
    new_orders = Order.objects.filter(order_date__date=today).count()
    pending_orders = Order.objects.filter(order_status='pending').count()
    cancelled_orders = Order.objects.filter(order_status='cancelled').count()
    total_orders = Order.objects.count()

    # Income
    today_income = Order.objects.filter(
        order_date__date=today, payment_status='paid'
    ).aggregate(total=Sum('orderitem__price'))['total'] or 0

    total_income = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('orderitem__price'))['total'] or 0

    # Customers
    new_customers = Customer.objects.filter(registered_at__date=today).count()
    total_customers = Customer.objects.count()

    # Latest orders (limit 20)
    latest_orders_raw = Order.objects.order_by('-id')[:20] 
    latest_orders = []
    for order in latest_orders_raw:
        total = order.orderitem_set.aggregate(total=Sum('price'))['total'] or 0
        if order.customer:
            shipping = Decimal('0.00') if total == 0 or total >= 75 else Decimal('50.00')
        else:
            shipping = 0
        total = total + shipping
        latest_orders.append({
            'order': order,
            'total': total
        })
    

    context = {
        'new_orders': new_orders,
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'total_orders': total_orders,
        'today_income': today_income,
        'total_income': total_income,
        'new_customers': new_customers,
        'total_customers': total_customers,
        'latest_orders': latest_orders,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@superadmin_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'

        # Basic validation
        if not name or len(name.strip()) < 3:
            messages.error(request, "Category name must be at least 3 characters.")
            return render(request, 'admin_panel/add_category.html', {'form_data': request.POST})

        try:
            Category.objects.create(
                name=name.strip(),
                description=description.strip(),
                is_active=is_active
            )
            messages.success(request, "Category added successfully.")
            return redirect('categories') 
        except Exception as e:
            messages.error(request, "Failed to add category. Please try again.")
            return render(request, 'admin_panel/add_category.html', {'form_data': request.POST})

    return render(request, 'admin_panel/add_category.html')

@superadmin_required
def categories(request):
    all_categories = Category.objects.all().order_by('-id')
    return render(request, 'admin_panel/categories.html', {'categories': all_categories})

@superadmin_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'

        # Basic validation
        if not name or len(name.strip()) < 3:
            messages.error(request, "Category name must be at least 3 characters.")
            return redirect('edit_category', category_id=category.id)

        category.name = name.strip()
        category.description = description.strip()
        category.is_active = is_active
        category.save()

        messages.success(request, "Category updated successfully.")
        return redirect('categories')

    return render(request, 'admin_panel/edit_category.html', {'category': category})

@superadmin_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    try:
        category.delete()
        messages.success(request, "Category deleted successfully.")
    except Exception as e:
        messages.error(request, "Failed to delete category.")
    return redirect('categories')

@superadmin_required
def add_product(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        category_id = request.POST.get('category')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        # Basic form validation
        if not (name and description and price and category_id and image):
            messages.error(request, "All fields are required.")
            return render(request, 'admin_panel/add_product.html', {'categories': categories, 'form_data': request.POST})

        try:
            category = get_object_or_404(Category, id=category_id)
            Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                is_active=is_active,
                image=image
            )
            messages.success(request, "Product added successfully.")
            return redirect('admin-products')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
    
    return render(request, 'admin_panel/add_product.html', {'categories': categories})

@superadmin_required
def products(request):
    products = Product.objects.filter().order_by('-id')
    return render(request, 'admin_panel/products.html', {'products': products})

@superadmin_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        category_id = request.POST['category']
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        category = Category.objects.get(id=category_id)
        
        product.name = name
        product.description = description
        product.price = price
        product.category = category
        product.is_active = is_active

        if image:
            product.image = image

        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('admin-products')

    categories = Category.objects.filter(is_active=True)
    return render(request, 'admin_panel/edit_product.html', {
        'product': product,
        'categories': categories,
    })

@superadmin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        product.delete()
        messages.success(request, "Product deleted successfully.")
    except Exception as e:
        messages.error(request, "Failed to delete product.")
    return redirect('admin-products')

@admin_login_required
def customers(request):
    customers = Customer.objects.all().order_by('-registered_at')
    return render(request, 'admin_panel/customers.html', {'customers': customers})

@admin_login_required
def contact_messages(request):
    messages = ContactMessage.objects.all().order_by('-submitted_at')
    return render(request, 'admin_panel/contact_messages.html', {'messages': messages})

@admin_login_required
def message_details(request, message_id):
    message_obj = get_object_or_404(ContactMessage, id=message_id)

    if request.method == 'POST':
        response_text = request.POST.get('response')
        
        # Send the email response
        try:
            send_mail(
                subject=f"Re: {message_obj.subject}",
                message=response_text,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[message_obj.email],
                fail_silently=False,
            )
            messages.success(request, "Response sent successfully to the user.")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")

        return redirect('message_details', message_id=message_id)

    return render(request, 'admin_panel/message_details.html', {'message': message_obj})

@admin_login_required
def orders(request):
    orders_raw = Order.objects.all().order_by('-id')
    
    # Annotate total price for each order manually
    orders = []
    for order in orders_raw:
        total = order.orderitem_set.aggregate(total=Sum('price'))['total'] or 0
        if order.customer:
            shipping = Decimal('0.00') if total == 0 or total >= 75 else Decimal('50.00')
        else:
            shipping = 0
        total = total + shipping
        orders.append({
            'order': order,
            'total': total
        })

    return render(request, 'admin_panel/orders.html', {'orders': orders})

@admin_login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.select_related('product').all()

    subtotal = sum(item.price for item in order_items)
    if order.customer:
        shipping_cost = Decimal('0.00') if subtotal == 0 or subtotal >= 75 else Decimal('50.00')
    else:
        shipping_cost = 0
    total = subtotal + shipping_cost

    # Determine if it's a walk-in customer
    is_walkin = order.customer is None

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
        'is_walkin': is_walkin,
    }

    return render(request, 'admin_panel/order_details.html', context)

@admin_login_required
def create_order(request):
    categories = Category.objects.all()

    # Group products by category
    products_by_category = {
        category.id: [
            {
                'id': product.id,
                'name': product.name,
                'price': float(product.price)
            }
            for product in Product.objects.filter(category=category)
        ]
        for category in categories
    }

    if request.method == 'POST':
        try:
            product_ids = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            payment_method = request.POST.get('payment_method')
            phone_number = request.POST.get('phone')  

            if not (product_ids and quantities and phone_number and payment_method):
                messages.error(request, "Please fill in all required fields.")
                return redirect('create_order')

            # Create the Order
            order = Order.objects.create(
                payment_method=payment_method,
                payment_status='paid',
                order_status='pending',
                billing_phone=phone_number
            )

            # Add OrderItems
            for product_id, qty in zip(product_ids, quantities):
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(qty),
                    price=product.price*int(qty)
                )

            messages.success(request, "Order created successfully.")
            return redirect('orders')  

        except Exception as e:
            messages.error(request, f"Error creating order: {str(e)}")
            return redirect('create_order')

    context = {
        'categories': categories,
        'products_json': json.dumps(products_by_category)
    }
    return render(request, 'admin_panel/create_order.html', context)

@admin_login_required
def mark_order_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.order_status == 'pending':
        order.order_status = 'delivered'
        order.payment_status = 'paid'
        order.save()
        messages.success(request, f"Order #{order.id} marked as delivered.")
    return redirect('order_details', order_id=order.id)

@admin_login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.order_status == 'pending':
        order.order_status = 'cancelled'
        order.save()
        messages.success(request, f"Order #{order.id} has been cancelled.")
    return redirect('order_details', order_id=order.id)

def resend_whatsapp(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        customer_number = order.shipping_phone.strip() if order.shipping_phone else ''
        
        if customer_number:
            try:
                parsed_number = phonenumbers.parse(customer_number, None)
                if phonenumbers.is_valid_number(parsed_number):
                    customer_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                    customer_whatsapp_message = resend_whatsapp_customer_message(order)
                    twilio_client.messages.create(
                        body=urllib.parse.unquote(customer_whatsapp_message),
                        from_=settings.TWILIO_WHATSAPP_NUMBER,
                        to=f"whatsapp:{customer_number}"
                    )
                    order.whatsapp_sent = True
                    order.save()
                    messages.success(request, f"WhatsApp message resent successfully to {customer_number}.")
                else:
                    messages.error(request, "Invalid customer phone number.")
            except TwilioRestException as e:
                if e.code == 30003:
                    messages.error(request, "Customer phone number is not registered with WhatsApp or is unreachable.")
                else:
                    messages.error(request, f"Failed to resend WhatsApp message: {str(e)}")
            except phonenumbers.NumberParseException as e:
                messages.error(request, "Failed to parse customer phone number.")
        else:
            messages.error(request, "No customer phone number provided.")
        
        return redirect('order_details', order_id=order.id)
    return redirect('order_details', order_id=order.id)

def resend_whatsapp_customer_message(order):
    order_items = OrderItem.objects.filter(order=order)
    message = f"🎉 Thank you for your order #{order.id}, {order.shipping_name}!\n\n"
    message += "Your order details:\n"

    total = 0
    for item in order_items:
        subtotal = item.quantity * item.price
        message += f"- {item.product.name} x {item.quantity} = ${subtotal:.2f}\n"
        total += subtotal

    
    shipping = Decimal('0.00') if total == 0 or total >= 75 else Decimal('50.00')
    final_total = total + shipping

    message += f"Subtotal: ${total:.2f}\n"
    message += f"Shipping: ${shipping:.2f}\n"
    message += f"Total: ${final_total:.2f}\n\n"
    message += f"Shipping to: {order.shipping_address}, {order.shipping_city}, {order.shipping_postal_code}\n\n"
    message += "Thank you,\nThe Cookie Barrel Team"

    return urllib.parse.quote(message)

@admin_login_required
def print_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Compute subtotal manually if not present
    subtotal = sum(item.price for item in order_items)

    # Determine shipping cost
    if order.customer:
        shipping_cost = 0 if subtotal >= 75 else 50
    else:
        shipping_cost = 0
    total = subtotal + shipping_cost

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    return render(request, 'admin_panel/invoice.html', context)

@admin_login_required
def download_receipt_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    subtotal = sum(item.price for item in order_items)

    if order.customer:
        shipping_cost = 0 if subtotal >= 75 else 50
    else:
        shipping_cost = 0

    total = subtotal + shipping_cost

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    template_path = 'admin_panel/invoice_pdf.html'
    
    # Render HTML to string
    template = get_template(template_path)
    html = template.render(context)

    # Create a response with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_order_{order_id}.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation failed')
    return response

@admin_login_required
def reports(request):
    today = datetime.today().date()
    default_start = (today - timedelta(days=6)).strftime('%m/%d/%Y')
    default_end = today.strftime('%m/%d/%Y')

    # GET values or defaults
    start_str = request.GET.get('start', default_start)
    end_str = request.GET.get('end', default_end)
    group_by = request.GET.get('group_by', 'day')

    # Parse to date
    try:
        start_date = datetime.strptime(start_str, "%m/%d/%Y").date()
        end_date = datetime.strptime(end_str, "%m/%d/%Y").date()
    except ValueError:
        start_date = today - timedelta(days=6)
        end_date = today

    # Base queryset
    orders = Order.objects.filter(order_date__date__range=[start_date, end_date])

    # Apply grouping
    if group_by == 'day':
        group_label = 'Date'
        grouped = orders.annotate(group=TruncDay('order_date'))
    elif group_by == 'week':
        group_label = 'Week'
        grouped = orders.annotate(group=TruncWeek('order_date'))
    elif group_by == 'month':
        group_label = 'Month'
        grouped = orders.annotate(group=TruncMonth('order_date'))
    elif group_by == 'year':
        group_label = 'Year'
        grouped = orders.annotate(group=TruncYear('order_date'))
    else:
        group_label = 'Group'
        grouped = orders.annotate(group=TruncDay('order_date'))  # fallback

    report_data = (
        grouped.values('group')
        .annotate(
            total_amount=Sum('orderitem__price'),
            total_orders=Count('id', distinct=True)  
        )
        .order_by('-group')
    )

    # Format group label
    formatted_data = []
    for row in report_data:
        group = row['group']
        if group_by == 'day':
            label = group.strftime('%b %d, %Y')
        elif group_by == 'week':
            label = f"Week {group.isocalendar().week}, {group.year}"
        elif group_by == 'month':
            label = group.strftime('%B %Y')
        elif group_by == 'year':
            label = str(group.year)
        else:
            label = str(group)

        formatted_data.append({
            'label': label,
            'total_orders': row['total_orders'],
            'total_amount': row['total_amount'] or 0
        })

    grand_total_orders = sum(item['total_orders'] for item in formatted_data)
    grand_total_amount = sum(item['total_amount'] for item in formatted_data)

    context = {
        'report_data': formatted_data,
        'start': start_str,
        'end': end_str,
        'group_by': group_by,
        'group_label': group_label,
        'grand_total_orders': grand_total_orders,
        'grand_total_amount': grand_total_amount,
    }
    return render(request, 'admin_panel/reports.html', context)

@admin_login_required
def download_report_pdf(request):
    today = datetime.today().date()
    default_start = (today - timedelta(days=6)).strftime('%m/%d/%Y')
    default_end = today.strftime('%m/%d/%Y')

    start_str = request.GET.get('start', default_start)
    end_str = request.GET.get('end', default_end)
    group_by = request.GET.get('group_by', 'day')

    try:
        start_date = datetime.strptime(start_str, "%m/%d/%Y").date()
        end_date = datetime.strptime(end_str, "%m/%d/%Y").date()
    except:
        start_date = today - timedelta(days=6)
        end_date = today

    orders = Order.objects.filter(order_date__date__range=[start_date, end_date])

    if group_by == 'day':
        grouped = orders.annotate(group=TruncDay('order_date'))
    elif group_by == 'week':
        grouped = orders.annotate(group=TruncWeek('order_date'))
    elif group_by == 'month':
        grouped = orders.annotate(group=TruncMonth('order_date'))
    elif group_by == 'year':
        grouped = orders.annotate(group=TruncYear('order_date'))
    else:
        grouped = orders.annotate(group=TruncDay('order_date'))

    report_data = (
        grouped.values('group')
        .annotate(
            total_amount=Sum('orderitem__price'),
            total_orders=Count('id', distinct=True)
        )
        .order_by('-group')
    )

    formatted_data = []
    for row in report_data:
        group = row['group']
        if group_by == 'day':
            label = group.strftime('%b %d, %Y')
        elif group_by == 'week':
            label = f"Week {group.isocalendar().week}, {group.year}"
        elif group_by == 'month':
            label = group.strftime('%B %Y')
        elif group_by == 'year':
            label = str(group.year)
        else:
            label = str(group)

        formatted_data.append({
            'label': label,
            'total_orders': row['total_orders'],
            'total_amount': row['total_amount'] or 0
        })

    grand_total_orders = sum(item['total_orders'] for item in formatted_data)
    grand_total_amount = sum(item['total_amount'] for item in formatted_data)
    
    template = get_template("admin_panel/report_pdf.html")
    html = template.render({
        'report_data': formatted_data,
        'start': start_str,
        'end': end_str,
        'group_by': group_by,
        'grand_total_orders': grand_total_orders,
        'grand_total_amount': grand_total_amount,
        'today': datetime.today().strftime('%b %d, %Y')
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response, encoding='UTF-8')
    return response
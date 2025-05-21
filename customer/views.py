from django.shortcuts import render, get_object_or_404, redirect
from admin_panel.models import Product, Category, Order, OrderItem
from django.db.models import Sum
from django.core.paginator import Paginator
from .models import ContactMessage, Customer, Cart
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from decimal import Decimal
import stripe
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    # Latest 3 products
    latest_products = Product.objects.filter(is_active=True).order_by('-id')[:3]

    # Top selling 10 products (based on total quantity sold)
    top_selling = (
        Product.objects.filter(is_active=True)
        .annotate(total_sold=Sum('orderitem__quantity'))
        .order_by('-total_sold')[:10]
    )

    context = {
        'latest_products': latest_products,
        'top_selling': top_selling,
    }
    return render(request, 'customer/home.html', context)

def header_categories(request):
    return {
        'header_categories': Category.objects.filter(is_active=True)
    }

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def about(request):
    return render(request, 'customer/about.html')

def cart(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to view your cart.")
        return redirect('login')

    cart_items = Cart.objects.filter(customer_id=customer_id).select_related('product')
    
    for item in cart_items:
        item.total_price = item.quantity * item.product.price

    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('0.00') if subtotal == 0 or subtotal >= 75 else Decimal('50.00')
    total = subtotal + shipping

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    }
    return render(request, 'customer/cart.html', context)

def clear_cart(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to clear your cart.")
        return redirect('login')
    
    Cart.objects.filter(customer_id=customer_id).delete()
    messages.success(request, "Your cart has been emptied.")
    return redirect('cart')

def update_cart_quantity(request, item_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to update your cart.")
        return redirect('login')
    
    quantity = int(request.POST.get('quantity', 1))
    

    cart_item = Cart.objects.filter(customer_id=customer_id, id=item_id).first()
    if cart_item:
        cart_item.quantity = max(1, quantity)
        cart_item.save()
        messages.success(request, f"Quantity updated for {cart_item.product.name}.")
    return redirect('cart')

def delete_cart_item(request, item_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to delete your cart item.")
        return redirect('login')
    
    Cart.objects.filter(customer_id=customer_id, id=item_id).delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

def add_to_cart(request, product_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to add items to your cart.")
        return redirect('login')

    customer = get_object_or_404(Customer, pk=customer_id)
    product = get_object_or_404(Product, pk=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    # Update or add item in cart
    cart_item, created = Cart.objects.get_or_create(
        customer=customer,
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity = quantity  # Overwrite with new value
        cart_item.save()

    messages.success(request, f"{product.name} updated in your cart.")
    return redirect('products')

def quick_add_to_cart(request, product_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login to add items to your cart.")
        return redirect('login')

    customer = get_object_or_404(Customer, pk=customer_id)
    product = get_object_or_404(Product, pk=product_id)

    cart_item, created = Cart.objects.get_or_create(
        customer=customer,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} added to cart.")
    return redirect('products')

def checkout_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please log in to proceed.")
        return redirect('login')
    
    # Fetch cart items for the logged-in customer
    cart_items = Cart.objects.filter(customer_id=customer_id)

    # Calculate subtotal
    for item in cart_items:
        item.total_price = item.quantity * item.product.price

    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('0.00') if subtotal == 0 or subtotal >= 75 else Decimal('50.00')
    total = subtotal + shipping

    if request.method == 'POST':
        form_data = {
            'billing_name': request.POST.get('name'),
            'billing_email': request.POST.get('email'),
            'billing_phone': request.POST.get('phone'),
            'billing_address': request.POST.get('address'),
            'shipping_name': request.POST.get('shipping_name'),
            'shipping_address': request.POST.get('shipping_address'),
            'shipping_city': request.POST.get('shipping_city'),
            'shipping_postal_code': request.POST.get('shipping_zip'),
            'shipping_phone': request.POST.get('shipping_phone'),
        }

        payment_method = request.POST.get('payment_method')

        if not all(form_data.values()) or not payment_method:
            messages.error(request, "All fields are required.")
            return render(request, 'customer/checkout.html', {
                'previous_data': form_data,
                'payment_method': payment_method,
                'cart_items': cart_items,
                'subtotal': subtotal,
                'shipping': shipping,
                'total': total
            })

        request.session['order_form_data'] = form_data

        if payment_method == 'cod':
            _create_order(customer_id, form_data, payment_method='cod', payment_status='unpaid')
            messages.success(request, "Order placed successfully with Cash on Delivery.")
            return redirect('my_orders')

        elif payment_method == 'online':
            return redirect('create_stripe_session')

    return render(request, 'customer/checkout.html', {
        'previous_data': {},
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    })


def create_stripe_session(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Login required.")
        return redirect('login')

    customer = Customer.objects.get(id=customer_id)
    cart_items = Cart.objects.filter(customer=customer_id)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('checkout')

    # Calculate subtotal
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping = 0 if subtotal >= 75 else 50

    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(item.product.price * 100),
                'product_data': {
                    'name': item.product.name,
                },
            },
            'quantity': item.quantity,
        })

    # Add shipping if applicable
    if shipping > 0:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(shipping * 100),
                'product_data': {
                    'name': 'Shipping',
                },
            },
            'quantity': 1,
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payment-success/'),
            cancel_url=request.build_absolute_uri('/payment-cancel/'),
            customer_email=customer.email,
        )
        return redirect(session.url, code=303)
    except Exception as e:
        messages.error(request, f"Stripe error: {str(e)}")
        return redirect('checkout')


def payment_success(request):
    customer_id = request.session.get('customer_id')
    form_data = request.session.get('order_form_data')

    if not customer_id or not form_data:
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('checkout')

    _create_order(customer_id, form_data, payment_method='online', payment_status='paid')
    del request.session['order_form_data']

    messages.success(request, "Payment successful and order placed.")
    return redirect('my_orders')


def payment_cancel(request):
    messages.error(request, "Payment was cancelled.")
    return redirect('checkout')

def _create_order(customer_id, form_data, payment_method, payment_status):
    customer = Customer.objects.get(id=customer_id)
    cart_items = Cart.objects.filter(customer=customer)

    if not cart_items.exists():
        return

    order = Order.objects.create(
        customer=customer,
        payment_method=payment_method,
        payment_status=payment_status,
        order_status='pending',
        **form_data
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=Decimal(item.product.price)
        )

    cart_items.delete()

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and phone and subject and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            messages.success(request, "Your message has been submitted successfully.")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'customer/contact.html', {'form_data': request.POST})

    return render(request, 'customer/contact.html')

def products(request):
    category_slug = request.GET.get('category')  # e.g., ?category=cookies
    products_query = Product.objects.filter(is_active=True).select_related('category')

    if category_slug:
        products_query = products_query.filter(category__name__iexact=category_slug)

    paginator = Paginator(products_query.order_by('-id'), 6)  # 6 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    categories = Category.objects.filter(is_active=True)

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'customer/products.html', context)

def product_details(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    # Get quantity from cart if customer is logged in
    previous_quantity = 1
    customer_id = request.session.get('customer_id')
    if customer_id:
        cart_item = Cart.objects.filter(customer_id=customer_id, product=product).first()
        if cart_item:
            previous_quantity = cart_item.quantity

    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:3]

    context = {
        'product': product,
        'related_products': related_products,
        'previous_quantity': previous_quantity
    }
    return render(request, 'customer/product_details.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, pk=category_id, is_active=True)
    product_list = Product.objects.filter(category=category, is_active=True).order_by('-id')

    # Set up pagination (6 products per page)
    paginator = Paginator(product_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'customer/category_products.html', context)

def signup_view(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        form_data = {'name': name, 'email': email}

        if not name or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return render(request, 'customer/signup.html', {'form_data': form_data})

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'customer/signup.html', {'form_data': form_data})

        if Customer.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'customer/signup.html', {'form_data': form_data})

        otp = str(random.randint(100000, 999999))

        # Save customer with OTP
        customer = Customer.objects.create(
            name=name,
            email=email,
            password=make_password(password1),
            is_verified=False,
            otp=otp
        )

        # Create verification link
        verify_url = request.build_absolute_uri(reverse('verify_otp') + f'?email={email}')

        # Send email
        try:
            send_mail(
                subject='Verify Your Account - The Cookie Barrel',
                message=f"Hi {name},\n\nYour OTP is: {otp}\n\nClick the link below to verify your account:\n{verify_url}\n\nThank you!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Account created. OTP sent to your email for verification.")
            return redirect('verify_otp')  # user will be prompted to enter OTP
        except Exception as e:
            customer.delete()  # rollback if email fails
            messages.error(request, "Failed to send OTP email. Please try again later.")
            return render(request, 'customer/signup.html', {'form_data': form_data})

    return render(request, 'customer/signup.html')

def verify_otp_view(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        return redirect('home')
    
    email = request.GET.get('email', '')  # email comes from query param or manual input

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        email = request.POST.get('email')

        try:
            customer = Customer.objects.get(email=email, is_verified=False)
        except Customer.DoesNotExist:
            messages.error(request, "No unverified account found for this email.")
            return redirect('verify_otp')

        if customer.otp == entered_otp:
            customer.is_verified = True
            customer.otp = None
            customer.save()
            messages.success(request, "Your account has been verified. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP.")

    return render(request, 'customer/verify_otp.html', {'email': email})

def login_view(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Store previous email input to repopulate field
        previous_data = {'email': email}

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            messages.error(request, "Invalid email.")
            return render(request, 'customer/login.html', {'form_data': previous_data})

        if not customer.is_verified:
            messages.warning(request, "Please verify your email to login.")
            return render(request, 'customer/login.html', {'form_data': previous_data})

        if not check_password(password, customer.password):
            messages.error(request, "Invalid password.")
            return render(request, 'customer/login.html', {'form_data': previous_data})

        # Store session data
        request.session['customer_id'] = customer.id
        request.session['customer_name'] = customer.name
        # messages.success(request, f"Welcome back, {customer.name}!")
        return redirect('home')

    return render(request, 'customer/login.html')

def logout_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')

def forgot_password(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        context = {'form_data': {'email': email}}

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return render(request, 'customer/forgot_password.html', context)

        otp = str(random.randint(100000, 999999))
        customer.otp = otp
        customer.save()

        # Send email
        reset_link = request.build_absolute_uri('/reset-password/')
        send_mail(
            'Password Reset Request',
            f'Dear {customer.name},\n\nYour OTP is: {otp}\n\nUse it at: {reset_link}\n\nThank You!',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.success(request, "An OTP has been sent to your email.")
        return redirect('reset_password')

    return render(request, 'customer/forgot_password.html')

def my_orders_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please log in to view your orders.")
        return redirect('login')

    orders_raw = Order.objects.filter(customer_id=customer_id).order_by('-id')
    
    orders = []
    for order in orders_raw:
        subtotal = order.orderitem_set.aggregate(total=Sum('price'))['total'] or 0
        total = subtotal if subtotal >= 75 else subtotal + 50
        orders.append({
            'order': order,
            'total': total
        })

    return render(request, 'customer/my_orders.html', {'orders': orders})

def order_details_view(request, order_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login first to your account.")
        return redirect('login')
    
    order = get_object_or_404(Order, id=order_id, customer_id=customer_id)
    order_items = OrderItem.objects.filter(order=order)

    cart_data = []
    subtotal = 0

    for item in order_items:
        total_price = item.quantity * item.price
        cart_data.append({
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': item.price,
            'total': total_price,
        })
        subtotal += total_price

    shipping = Decimal('0.00') if subtotal == 0 or subtotal >= 75 else Decimal('50.00')
    total = subtotal + shipping

    context = {
        'order': order,
        'cart_data': cart_data,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    }
    return render(request, 'customer/order_details.html', context)

def cancel_order_view(request, order_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')

    order = get_object_or_404(Order, id=order_id, customer_id=customer_id)

    if order.order_status != 'pending':
        messages.error(request, 'Only pending orders can be cancelled.')
    else:
        order.order_status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled.')

    return redirect('order_details_customer', order_id=order.id)

def reset_password_view(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        return redirect('home')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_pass = request.POST.get('new_password1')
        confirm_pass = request.POST.get('new_password2')

        if new_pass != confirm_pass:
            messages.error(request, "Passwords do not match.")
            return render(request, 'customer/reset_password.html')

        try:
            customer = Customer.objects.get(otp=otp)
        except Customer.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return render(request, 'customer/reset_password.html')

        customer.password = make_password(new_pass)
        customer.otp = None
        customer.save()
        messages.success(request, "Password has been reset. Please login.")
        return redirect('login')

    return render(request, 'customer/reset_password.html')

def terms_conditions_view(request):
    return render(request, 'customer/terms_conditions.html')

def privacy_policy_view(request):
    return render(request, 'customer/privacy_policy.html')

def profile_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login first to your account.")
        return redirect('login')
    
    customer = Customer.objects.get(id=customer_id)
    return render(request, 'customer/profile.html', {'customer': customer})

def edit_profile_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login first to your account.")
        return redirect('login')

    customer = Customer.objects.get(id=customer_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if not name:
            messages.error(request, "Name is required.")
            return render(request, 'customer/edit_profile.html', {
                'form_data': {'name': name, 'phone': phone, 'address': address, 'email': customer.email}
            })

        customer.name = name
        customer.phone = phone
        customer.address = address
        customer.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    # Populate initial form
    form_data = {
        'name': customer.name,
        'phone': customer.phone,
        'address': customer.address,
        'email': customer.email
    }
    return render(request, 'customer/edit_profile.html', {'form_data': form_data})

def change_password_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please login first to your account.")
        return redirect('login')

    customer = Customer.objects.get(id=customer_id)

    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass1 = request.POST.get('new_password1')
        new_pass2 = request.POST.get('new_password2')

        if not check_password(old_pass, customer.password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'customer/change_password.html')

        if new_pass1 != new_pass2:
            messages.error(request, "New passwords do not match.")
            return render(request, 'customer/change_password.html')

        customer.password = make_password(new_pass1)
        customer.save()
        messages.success(request, "Password changed successfully.")
        return redirect('profile')

    return render(request, 'customer/change_password.html')

def search_results(request):
    query = request.GET.get('q')
    results = []

    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).distinct()

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'customer/search_results.html', context)
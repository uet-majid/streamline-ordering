from django.db import models

class AdminUser(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('staff', 'Staff'),
    ]

    username = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]

    customer = models.ForeignKey("customer.Customer", on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    whatsapp_sent = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')

    # Billing Info
    billing_name = models.CharField(max_length=100, null=True, blank=True)
    billing_email = models.EmailField(null=True, blank=True)
    billing_phone = models.CharField(max_length=20, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)

    # Shipping Info
    shipping_name = models.CharField(max_length=100, null=True, blank=True)
    shipping_phone = models.CharField(max_length=20, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    shipping_city = models.CharField(max_length=100, null=True, blank=True)
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.order_status}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_id.name} x {self.quantity}"
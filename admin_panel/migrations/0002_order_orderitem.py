# Generated by Django 5.2.1 on 2025-05-10 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('order_status', models.CharField(choices=[('pending', 'Pending'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('whatsapp_sent', models.BooleanField(default=False)),
                ('payment_status', models.CharField(choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid', max_length=10)),
                ('payment_method', models.CharField(choices=[('cod', 'Cash on Delivery'), ('online', 'Online Payment')], default='cod', max_length=10)),
                ('billing_name', models.CharField(blank=True, max_length=100, null=True)),
                ('billing_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('billing_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('billing_address', models.TextField(blank=True, null=True)),
                ('shipping_name', models.CharField(blank=True, max_length=100, null=True)),
                ('shipping_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('shipping_address', models.TextField(blank=True, null=True)),
                ('shipping_city', models.CharField(blank=True, max_length=100, null=True)),
                ('shipping_postal_code', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]

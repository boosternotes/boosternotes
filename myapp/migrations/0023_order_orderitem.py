# Generated manually — Order + OrderItem models were missing from migrations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0022_couponusage'),
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order_number', models.CharField(editable=False, max_length=20, unique=True)),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('mobile', models.CharField(max_length=15)),
                ('address', models.TextField(blank=True, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('pincode', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(default='India', max_length=100)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('grand_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(
                    choices=[('razorpay', 'Razorpay'), ('cod', 'Cash on Delivery')],
                    default='razorpay', max_length=20)),
                ('razorpay_order_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_signature', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'), ('paid', 'Paid'), ('processing', 'Processing'),
                        ('shipped', 'Shipped'), ('delivered', 'Delivered'),
                        ('cancelled', 'Cancelled'), ('refunded', 'Refunded'),
                    ],
                    default='pending', max_length=20)),
                ('is_paid', models.BooleanField(default=False)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('coupon', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='myapp.coupon')),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='orders',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('item_type', models.CharField(
                    choices=[('pdf', 'E-Library PDF'), ('book', 'Hard Copy Book')],
                    max_length=10)),
                ('item_id', models.CharField(max_length=100)),
                ('item_name', models.CharField(max_length=300)),
                ('item_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='myapp.order')),
            ],
            options={
                'verbose_name': 'Order Item',
                'verbose_name_plural': 'Order Items',
            },
        ),
    ]

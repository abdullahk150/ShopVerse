"""
models.py - E-Commerce Platform Database Schema
============================================================
Entities: UserProfile, Category, Product, ProductImage,
          Cart, CartItem, Order, OrderItem, Payment,
          Review, VendorProfile, Address
============================================================
All tables are in 3NF (Third Normal Form).
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


# ─────────────────────────────────────────────
# ROLE CHOICES  (Role-Based Access Control)
# ─────────────────────────────────────────────
class UserProfile(models.Model):
    """
    Extends Django's built-in User model.
    Implements RBAC: customer / vendor / admin.
    """
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor',   'Vendor'),
        ('admin',    'Admin'),
    ]

    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role        = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone       = models.CharField(max_length=20, blank=True)
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = 'User Profile'

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_vendor(self):
        return self.role == 'vendor'

    @property
    def is_customer(self):
        return self.role == 'customer'


# ─────────────────────────────────────────────
# VENDOR PROFILE
# ─────────────────────────────────────────────
class VendorProfile(models.Model):
    """
    Extra vendor-specific data (1:1 with UserProfile for vendors).
    Supports admin approval workflow.
    """
   
    ]

    user_profile    = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='vendor_profile')
    store_name      = models.CharField(max_length=150)
    store_slug      = models.SlugField(max_length=160, unique=True)
    description     = models.TextField(blank=True)
    logo            = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_sales     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_at     = models.DateTimeField(null=True, blank=True)
    approved_by     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_vendors')

    class Meta:
        db_table = 'vendor_profile'
        verbose_name = 'Vendor Profile'

    def __str__(self):
        return f"{self.store_name} [{self.status}]"


# ─────────────────────────────────────────────
# ADDRESS
# ─────────────────────────────────────────────
class Address(models.Model):
    """
    Shipping/billing addresses for customers.
    Separated to avoid redundancy in Orders.
    """
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name    = models.CharField(max_length=150)
    street       = models.CharField(max_length=255)
    city         = models.CharField(max_length=100)
    state        = models.CharField(max_length=100)
    postal_code  = models.CharField(max_length=20)
    country      = models.CharField(max_length=100, default='Pakistan')
    is_default   = models.BooleanField(default=False)

    class Meta:
        db_table = 'address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.country}"


# ─────────────────────────────────────────────
# CATEGORY  (self-referential for subcategories)
# ─────────────────────────────────────────────
class Category(models.Model):
    """
    Product categories with optional parent (supports sub-categories).
    """
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent      = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────────
class Product(models.Model):
    """
    Core product listing. Linked to vendor and category.
    Tracks stock for inventory management.
    """
    STATUS_CHOICES = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
        ('sold_out', 'Sold Out'),
    ]

    vendor      = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_pct= models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage (0-100)")
    stock       = models.PositiveIntegerField(default=0)
    sku         = models.CharField(max_length=100, unique=True, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    thumbnail   = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    weight_kg   = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        if self.discount_pct > 0:
            return round(self.price * (1 - self.discount_pct / 100), 2)
        return self.price

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


# ─────────────────────────────────────────────
# PRODUCT IMAGE  (multiple images per product)
# ─────────────────────────────────────────────
class ProductImage(models.Model):
    """
    Multiple gallery images per product.
    Normalized: separated from Product table.
    """
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image       = models.ImageField(upload_to='products/gallery/')
    alt_text    = models.CharField(max_length=200, blank=True)
    is_primary  = models.BooleanField(default=False)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'product_image'
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"


# ─────────────────────────────────────────────
# SHOPPING CART
# ─────────────────────────────────────────────
class Cart(models.Model):
    """
    One active cart per user (session-based for guests too).
    """
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart'

    def __str__(self):
        return f"Cart of {self.user.username if self.user else 'Guest'}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    """
    Individual line items in a cart.
    """
    cart        = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity    = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_item'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def line_total(self):
        return self.product.discounted_price * self.quantity


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────
class Order(models.Model):
    """
    Placed orders with full status tracking.
    Stores a snapshot of address at time of order (denormalized intentionally).
    """
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('refunded',   'Refunded'),
    ]

    customer        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number    = models.CharField(max_length=20, unique=True)
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Shipping address snapshot
    ship_name       = models.CharField(max_length=150)
    ship_street     = models.CharField(max_length=255)
    ship_city       = models.CharField(max_length=100)
    ship_state      = models.CharField(max_length=100)
    ship_postal     = models.CharField(max_length=20)
    ship_country    = models.CharField(max_length=100, default='Pakistan')
    ship_phone      = models.CharField(max_length=20, blank=True)

    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount    = models.DecimalField(max_digits=12, decimal_places=2)

    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer', 'status']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = 'ORD-' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Line items within an order.
    Price is stored at time of purchase (immutable snapshot).
    """
    order           = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product         = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    vendor          = models.ForeignKey(VendorProfile, on_delete=models.SET_NULL, null=True)
    product_name    = models.CharField(max_length=200)   # snapshot
    unit_price      = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot
    quantity        = models.PositiveIntegerField()
    line_total      = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'order_item'

    def __str__(self):
        return f"{self.quantity} × {self.product_name} in {self.order}"

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────
class Payment(models.Model):
    """
    Payment record for each order.
    Separated from Order for PCI DSS compliance.
    """
    METHOD_CHOICES = [
        ('cod',          'Cash on Delivery'),
        ('credit_card',  'Credit Card'),
        ('debit_card',   'Debit Card'),
        ('bank_transfer','Bank Transfer'),
        ('easypaisa',    'EasyPaisa'),
        ('jazzcash',     'JazzCash'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('refunded',  'Refunded'),
    ]

    order           = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method          = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id  = models.CharField(max_length=200, blank=True)
    paid_at         = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return f"Payment for {self.order} - {self.status}"


# ─────────────────────────────────────────────
# REVIEW & RATING
# ─────────────────────────────────────────────
class Review(models.Model):
    """
    Customer reviews on purchased products.
    One review per customer per product.
    """
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating      = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title       = models.CharField(max_length=150, blank=True)
    body        = models.TextField()
    is_verified = models.BooleanField(default=False, help_text="Verified purchase review")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'
        unique_together = ('product', 'customer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ by {self.customer.username} on {self.product.name}"


# ─────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────
class Wishlist(models.Model):
    """
    Customer's saved/wishlisted products.
    """
    customer    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist'
        unique_together = ('customer', 'product')

    def __str__(self):
        return f"{self.customer.username} ♥ {self.product.name}"

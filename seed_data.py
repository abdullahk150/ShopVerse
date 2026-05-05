"""
seed_data.py — Sample data for ShopVerse
Run with: python manage.py shell < seed_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_platform.settings')

from django.contrib.auth.models import User
from ecommerce.models import (
    UserProfile, VendorProfile, Category, Product
)

print("🌱 Seeding ShopVerse database...")

# ── Admin user ────────────────────────────────
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@shopverse.pk', 'Admin@1234')
    UserProfile.objects.create(user=admin, role='admin', phone='0300-0000000')
    print("  ✅ Admin user created  (username: admin | password: Admin@1234)")

# ── Vendor user ───────────────────────────────
if not User.objects.filter(username='vendor1').exists():
    v_user = User.objects.create_user('vendor1', 'vendor@shopverse.pk', 'Vendor@1234',
                                      first_name='Ali', last_name='Traders')
    v_profile = UserProfile.objects.create(user=v_user, role='vendor', phone='0311-1111111')
    vendor = VendorProfile.objects.create(
        user_profile=v_profile,
        store_name='Ali Traders',
        store_slug='ali-traders',
        description='Quality electronics and gadgets at the best prices.',
        status='approved'
    )
    print("  ✅ Vendor created  (username: vendor1 | password: Vendor@1234)")
else:
    vendor = VendorProfile.objects.filter(store_slug='ali-traders').first()

# ── Customer user ─────────────────────────────
if not User.objects.filter(username='customer1').exists():
    c_user = User.objects.create_user('customer1', 'customer@shopverse.pk', 'Customer@1234',
                                      first_name='Sara', last_name='Khan')
    UserProfile.objects.create(user=c_user, role='customer', phone='0322-2222222')
    print("  ✅ Customer created  (username: customer1 | password: Customer@1234)")

# ── Categories ────────────────────────────────
cats = [
    ('Electronics',  'electronics',  'Gadgets and devices'),
    ('Clothing',     'clothing',     'Fashion for men and women'),
    ('Books',        'books',        'Academic and leisure reading'),
    ('Home & Living','home-living',  'Furniture and decor'),
    ('Sports',       'sports',       'Sports and fitness equipment'),
    ('Beauty',       'beauty',       'Skincare and cosmetics'),
    ('Groceries',    'groceries',    'Fresh and packaged food'),
    ('Toys',         'toys',         "Children's toys and games"),
]

category_objs = {}
for name, slug, desc in cats:
    cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc})
    category_objs[slug] = cat

print(f"  ✅ {len(cats)} categories created")

# ── Products ──────────────────────────────────
if vendor:
    products_data = [
        ('Wireless Bluetooth Headphones', 'wireless-bluetooth-headphones',
         'High-quality over-ear headphones with active noise cancellation, 30-hour battery life.',
         3500, 10, 25, 'electronics'),
        ('Smart LED TV 43"', 'smart-led-tv-43',
         '4K Ultra HD Smart TV with built-in WiFi, Netflix, YouTube. Crystal clear display.',
         45000, 5, 3, 'electronics'),
        ('USB-C Fast Charger 65W', 'usb-c-fast-charger-65w',
         'Universal fast charger compatible with laptops, phones, and tablets.',
         1200, 15, 50, 'electronics'),
        ('Running Shoes Pro', 'running-shoes-pro',
         'Lightweight breathable running shoes with memory foam insole. Available in all sizes.',
         4500, 20, 30, 'sports'),
        ('Yoga Mat Premium', 'yoga-mat-premium',
         'Anti-slip 6mm thick yoga mat with carrying strap. Eco-friendly material.',
         1800, 0, 40, 'sports'),
        ('Python Programming Book', 'python-programming-book',
         'Comprehensive guide to Python 3 for beginners and advanced programmers.',
         950, 0, 100, 'books'),
        ('Database Systems Textbook', 'database-systems-textbook',
         'Complete reference for relational databases, SQL, and modern DBMS concepts.',
         1200, 5, 60, 'books'),
        ('Men\'s Casual Shirt', 'mens-casual-shirt',
         'Premium cotton casual shirt. Available in S, M, L, XL. Multiple colors.',
         1500, 10, 80, 'clothing'),
        ('Women\'s Kurti Pack', 'womens-kurti-pack',
         'Pack of 3 printed cotton kurtis. Comfortable everyday wear.',
         2200, 0, 45, 'clothing'),
        ('Moisturizing Face Cream', 'moisturizing-face-cream',
         'SPF 30 daily moisturizer for all skin types. Dermatologist tested.',
         850, 0, 120, 'beauty'),
    ]

    count = 0
    for name, slug, desc, price, disc, stock, cat_slug in products_data:
        if not Product.objects.filter(slug=slug).exists():
            Product.objects.create(
                vendor=vendor,
                category=category_objs[cat_slug],
                name=name,
                slug=slug,
                description=desc,
                price=price,
                discount_pct=disc,
                stock=stock,
                status='active',
                sku=f'SKU-{slug[:8].upper()}'
            )
            count += 1

    print(f"  ✅ {count} products added")

print("\n🎉 Seed data loaded successfully!")
print("\n📋 Login Credentials:")
print("   Admin:    username=admin     | password=Admin@1234     | URL: /admin-panel/")
print("   Vendor:   username=vendor1   | password=Vendor@1234    | URL: /vendor/")
print("   Customer: username=customer1 | password=Customer@1234  | URL: /dashboard/")



#dadwadawdadwawd
#dawdawdwadaddawd#dawd
#dhawdwaawdws
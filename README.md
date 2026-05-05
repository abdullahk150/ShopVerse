# ShopVerse — E-Commerce Platform
### DBMS Semester Project | CYS 2024

**Students:** Ahmad Ali Khan (2024063) · Abdullah Kaleem (2024326) · Muhammad Danish (2024372) · Abbas Alamgir (2024004)

---

## Tech Stack
| Layer      | Technology          |
|------------|---------------------|
| Database   | PostgreSQL          |
| Backend    | Django 4.2 (Python) |
| Frontend   | HTML5 + CSS3 + JS   |
| Auth       | Django Auth + RBAC  |

---

## Project Structure

```

    ├── models.py                      ← All DB models (13 tables)
    ├── views.py                       ← All views / business logic
    ├── urls.py                        ← URL routing
    ├── forms.py                       ← All forms
    ├── admin.py                       ← Django admin config
    ├── context_processors.py
    ├── static/css/main.css            ← Full stylesheet
    └── templates/ecommerce/
        ├── base.html
        ├── home.html
        ├── auth/         (login, register_customer, register_vendor)
        ├── products/     (list, detail, category)
        ├── cart/         (cart, checkout)
        ├── orders/       (list, detail, confirmation)
        ├── dashboard/    (customer, profile)
        ├── vendor/       (dashboard, product_form, pending)
        └── admin_panel/  (dashboard, users, orders)
```

---

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL database
```bash
psql -U postgres
CREATE DATABASE ecommerce_db;
\q
```

### 3. (Optional) Run raw SQL schema directly
```bash
psql -U postgres -d ecommerce_db -f schema.sql
```

### 4. Configure database credentials
Edit `ecommerce_platform/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Run Django migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (Admin)
```bash
python manage.py createsuperuser
```
After creation, log in and go to `/admin/` to set the user's role to `admin` via UserProfile, OR run:
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from ecommerce.models import UserProfile
>>> u = User.objects.get(username='your_superuser')
>>> UserProfile.objects.create(user=u, role='admin')
```

### 7. Load sample data (optional)
```bash
python manage.py shell < seed_data.py
```

### 8. Run the development server
```bash
python manage.py runserver
```
Visit: **http://127.0.0.1:8000**

---

## User Roles & Access

| Role     | Register At              | Capabilities                                          |
|----------|--------------------------|-------------------------------------------------------|
| Customer | `/register/`             | Browse, cart, checkout, orders, reviews, wishlist     |
| Vendor   | `/register/vendor/`      | All customer features + manage own products/store     |
| Admin    | Created via Django shell | Approve vendors, manage all users/orders, full access |

---

## Key URLs

| URL                    | Description              |
|------------------------|--------------------------|
| `/`                    | Home page                |
| `/products/`           | Product listing + filter |
| `/products/<slug>/`    | Product detail + reviews |
| `/cart/`               | Shopping cart            |
| `/checkout/`           | Checkout                 |
| `/orders/`             | My orders                |
| `/dashboard/`          | Customer dashboard       |
| `/vendor/`             | Vendor panel             |
| `/admin-panel/`        | Custom admin panel       |
| `/admin/`              | Django admin             |
| `/login/`              | Login                    |
| `/register/`           | Customer registration    |
| `/register/vendor/`    | Vendor registration      |

---

## Database Schema (13 Tables)

| Table            | Description                                  |
|------------------|----------------------------------------------|
| `user_profile`   | Extends auth_user with RBAC role             |
| `vendor_profile` | Vendor store info + approval workflow        |
| `address`        | Customer shipping/billing addresses          |
| `category`       | Self-referential product categories          |
| `product`        | Core product with pricing & inventory        |
| `product_image`  | Multiple images per product                  |
| `cart`           | Active cart (user or guest session)          |
| `cart_item`      | Line items in cart                           |
| `order`          | Placed orders with address snapshot          |
| `order_item`     | Order line items with price snapshot         |
| `payment`        | Payment record (PCI DSS separated)           |
| `review`         | Customer reviews & star ratings              |
| `wishlist`       | Customer saved products                      |

All tables satisfy **3NF (Third Normal Form)**.

---

## ER Diagram Entities & Relationships

```
User (auth_user)
 └─1:1── UserProfile (role: customer/vendor/admin)
              └─1:1── VendorProfile (store, approval status)
                           └─1:N── Product
                                        └─1:N── ProductImage
                                        └─1:N── OrderItem
                                        └─1:N── Review
                                        └─1:N── CartItem
                                        └─1:N── Wishlist

User ──1:N── Address
User ──1:1── Cart ──1:N── CartItem ──N:1── Product
User ──1:N── Order ──1:N── OrderItem
             Order ──1:1── Payment
User ──1:N── Review ──N:1── Product
User ──1:N── Wishlist ──N:1── Product
Category ──1:N── Product
Category ──1:N── Category (self-referential subcategories)
```

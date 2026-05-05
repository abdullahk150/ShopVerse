"""
views.py - All views for the E-Commerce Platform
Covers: Home, Products, Cart, Checkout, Orders,
        Vendor Dashboard, Admin Panel, Auth
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import json

from .models import (
    UserProfile, VendorProfile, Category, Product,
    Cart, CartItem, Order, OrderItem, Payment, Review, Wishlist, Address
)
from .forms import (
    CustomerRegistrationForm, VendorRegistrationForm, UserProfileUpdateForm,
    ProductForm, AddressForm, CheckoutForm, ReviewForm, ProductFilterForm
)


# ═══════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def get_user_role(user):
    try:
        return user.profile.role
    except Exception:
        return None


def require_role(*roles):
    """Decorator factory for role-based access."""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            role = get_user_role(request.user)
            if role not in roles and not request.user.is_superuser:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


# ═══════════════════════════════════════════════════════
#  HOME & GENERAL
# ═══════════════════════════════════════════════════════
def home(request):
    categories   = Category.objects.filter(is_active=True, parent=None)[:8]
    featured     = Product.objects.filter(status='active').order_by('-created_at')[:8]
    top_rated    = Product.objects.filter(status='active').annotate(avg_r=Avg('reviews__rating')).order_by('-avg_r')[:4]
    return render(request, 'ecommerce/home.html', {
        'categories': categories,
        'featured_products': featured,
        'top_rated': top_rated,
    })


# ═══════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════
def register_customer(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = CustomerRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
        return redirect('home')
    return render(request, 'ecommerce/auth/register_customer.html', {'form': form})


def register_vendor(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = VendorRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.info(request, "Your vendor account is pending admin approval.")
        return redirect('home')
    return render(request, 'ecommerce/auth/register_vendor.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    return render(request, 'ecommerce/auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')


# ═══════════════════════════════════════════════════════
#  PRODUCTS
# ═══════════════════════════════════════════════════════
def product_list(request):
    products   = Product.objects.filter(status='active').select_related('category', 'vendor')
    categories = Category.objects.filter(is_active=True)
    form       = ProductFilterForm(request.GET)

    q          = request.GET.get('q', '')
    cat_id     = request.GET.get('category', '')
    min_price  = request.GET.get('min_price', '')
    max_price  = request.GET.get('max_price', '')
    sort       = request.GET.get('sort', '')

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )
    if cat_id:
        products = products.filter(category_id=cat_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'rating':
        products = products.annotate(avg_r=Avg('reviews__rating')).order_by('-avg_r')

    paginator = Paginator(products, 12)
    page      = request.GET.get('page', 1)
    products  = paginator.get_page(page)

    return render(request, 'ecommerce/products/list.html', {
        'products': products,
        'categories': categories,
        'form': form,
        'q': q,
        'selected_cat': cat_id,
    })


def product_detail(request, slug):
    product      = get_object_or_404(Product, slug=slug, status='active')
    reviews      = product.reviews.select_related('customer').order_by('-created_at')
    related      = Product.objects.filter(category=product.category, status='active').exclude(id=product.id)[:4]
    review_form  = ReviewForm()
    user_review  = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, customer=request.user).first()

    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid() and not user_review:
            r = review_form.save(commit=False)
            r.product  = product
            r.customer = request.user
            # Mark as verified if customer purchased this product
            r.is_verified = OrderItem.objects.filter(
                order__customer=request.user, product=product,
                order__status='delivered'
            ).exists()
            r.save()
            messages.success(request, "Your review has been submitted!")
            return redirect('product_detail', slug=slug)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(customer=request.user, product=product).exists()

    return render(request, 'ecommerce/products/detail.html', {
        'product': product,
        'reviews': reviews,
        'related_products': related,
        'review_form': review_form,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
    })


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, status='active')
    paginator = Paginator(products, 12)
    page     = request.GET.get('page', 1)
    products = paginator.get_page(page)
    return render(request, 'ecommerce/products/category.html', {
        'category': category,
        'products': products,
    })


# ═══════════════════════════════════════════════════════
#  CART
# ═══════════════════════════════════════════════════════
def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'ecommerce/cart/cart.html', {'cart': cart})


@require_POST
def add_to_cart(request, product_id):
    product  = get_object_or_404(Product, id=product_id, status='active')
    cart     = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > product.stock:
        messages.error(request, f"Only {product.stock} item(s) available in stock.")
        return redirect('product_detail', slug=product.slug)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = min(item.quantity + quantity, product.stock)
    else:
        item.quantity = quantity
    item.save()

    messages.success(request, f"'{product.name}' added to cart!")
    return redirect('cart')


@require_POST
def update_cart(request, item_id):
    item     = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        item.delete()
        messages.info(request, "Item removed from cart.")
    else:
        item.quantity = min(quantity, item.product.stock)
        item.save()
    return redirect('cart')


@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')


# ═══════════════════════════════════════════════════════
#  CHECKOUT & ORDERS
# ═══════════════════════════════════════════════════════
@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    addresses = Address.objects.filter(user=request.user)
    form      = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd           = form.cleaned_data
        shipping_cost= Decimal('150.00')
        tax_rate     = Decimal('0.0')   # adjust as needed
        subtotal     = cart.subtotal
        tax_amount   = subtotal * tax_rate
        total        = subtotal + shipping_cost + tax_amount

        # Create order
        order = Order.objects.create(
            customer     = request.user,
            status       = 'pending',
            ship_name    = cd['full_name'],
            ship_street  = cd['street'],
            ship_city    = cd['city'],
            ship_state   = cd['state'],
            ship_postal  = cd['postal_code'],
            ship_country = cd['country'],
            ship_phone   = cd.get('phone', ''),
            subtotal     = subtotal,
            shipping_cost= shipping_cost,
            tax_amount   = tax_amount,
            total_amount = total,
            notes        = cd.get('notes', ''),
        )

        # Create order items & decrement stock
        for item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order        = order,
                product      = item.product,
                vendor       = item.product.vendor,
                product_name = item.product.name,
                unit_price   = item.product.discounted_price,
                quantity     = item.quantity,
            )
            item.product.stock -= item.quantity
            item.product.save()

        # Create payment record
        Payment.objects.create(
            order  = order,
            method = cd['payment_method'],
            amount = total,
            status = 'pending' if cd['payment_method'] != 'cod' else 'pending',
        )

        # Clear cart
        cart.items.all().delete()

        messages.success(request, f"Order #{order.order_number} placed successfully!")
        return redirect('order_confirmation', order_id=order.id)

    shipping_cost = Decimal('150.00')
    return render(request, 'ecommerce/cart/checkout.html', {
        'cart': cart,
        'form': form,
        'addresses': addresses,
        'shipping_cost': shipping_cost,
    })


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'ecommerce/orders/confirmation.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'ecommerce/orders/list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'ecommerce/orders/detail.html', {'order': order})


# ═══════════════════════════════════════════════════════
#  CUSTOMER DASHBOARD
# ═══════════════════════════════════════════════════════
@login_required
def customer_dashboard(request):
    profile      = request.user.profile
    recent_orders= Order.objects.filter(customer=request.user).order_by('-created_at')[:5]
    wishlist     = Wishlist.objects.filter(customer=request.user).select_related('product')
    return render(request, 'ecommerce/dashboard/customer.html', {
        'profile': profile,
        'recent_orders': recent_orders,
        'wishlist': wishlist,
    })


@login_required
def profile_update(request):
    profile = request.user.profile
    form    = UserProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('customer_dashboard')
    return render(request, 'ecommerce/dashboard/profile.html', {'form': form})


# ═══════════════════════════════════════════════════════
#  WISHLIST
# ═══════════════════════════════════════════════════════
@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(customer=request.user, product=product)
    if not created:
        obj.delete()
        msg = "Removed from wishlist."
    else:
        msg = "Added to wishlist!"
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ═══════════════════════════════════════════════════════
#  VENDOR DASHBOARD
# ═══════════════════════════════════════════════════════
@require_role('vendor')
def vendor_dashboard(request):
    vendor   = get_object_or_404(VendorProfile, user_profile=request.user.profile)
    if vendor.status != 'approved':
        return render(request, 'ecommerce/vendor/pending.html', {'vendor': vendor})

    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    orders   = OrderItem.objects.filter(vendor=vendor).select_related('order').order_by('-order__created_at')[:10]
    total_revenue = sum(i.line_total for i in OrderItem.objects.filter(vendor=vendor))
    return render(request, 'ecommerce/vendor/dashboard.html', {
        'vendor': vendor,
        'products': products,
        'recent_orders': orders,
        'total_revenue': total_revenue,
    })


@require_role('vendor')
def vendor_add_product(request):
    vendor = get_object_or_404(VendorProfile, user_profile=request.user.profile)
    if vendor.status != 'approved':
        return redirect('vendor_dashboard')
    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        product        = form.save(commit=False)
        product.vendor = vendor
        product.save()
        messages.success(request, f"Product '{product.name}' added successfully!")
        return redirect('vendor_dashboard')
    return render(request, 'ecommerce/vendor/product_form.html', {'form': form, 'action': 'Add'})


@require_role('vendor')
def vendor_edit_product(request, product_id):
    vendor  = get_object_or_404(VendorProfile, user_profile=request.user.profile)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    form    = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully!")
        return redirect('vendor_dashboard')
    return render(request, 'ecommerce/vendor/product_form.html', {'form': form, 'action': 'Edit', 'product': product})


@require_role('vendor')
def vendor_delete_product(request, product_id):
    vendor  = get_object_or_404(VendorProfile, user_profile=request.user.profile)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted.")
    return redirect('vendor_dashboard')


# ═══════════════════════════════════════════════════════
#  ADMIN PANEL (custom, role=admin)
# ═══════════════════════════════════════════════════════
@require_role('admin')
def admin_dashboard(request):
    total_users    = User.objects.count()
    total_orders   = Order.objects.count()
    total_products = Product.objects.count()
    total_vendors  = VendorProfile.objects.filter(status='approved').count()
    pending_vendors= VendorProfile.objects.filter(status='pending')
    recent_orders  = Order.objects.order_by('-created_at')[:10]
    return render(request, 'ecommerce/admin_panel/dashboard.html', {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_vendors': total_vendors,
        'pending_vendors': pending_vendors,
        'recent_orders': recent_orders,
    })


@require_role('admin')
def admin_approve_vendor(request, vendor_id):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            vendor.status      = 'approved'
            vendor.approved_at = timezone.now()
            vendor.approved_by = request.user
            vendor.save()
            messages.success(request, f"Vendor '{vendor.store_name}' approved.")
        elif action == 'reject':
            vendor.status = 'rejected'
            vendor.save()
            messages.warning(request, f"Vendor '{vendor.store_name}' rejected.")
    return redirect('admin_dashboard')


@require_role('admin')
def admin_users(request):
    users = User.objects.select_related('profile').order_by('-date_joined')
    return render(request, 'ecommerce/admin_panel/users.html', {'users': users})


@require_role('admin')
def admin_orders(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')
    return render(request, 'ecommerce/admin_panel/orders.html', {'orders': orders})


@require_role('admin')
def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.order_number} updated to {new_status}.")
    return redirect('admin_orders')

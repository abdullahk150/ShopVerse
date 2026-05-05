"""
urls.py - URL Routing for E-Commerce Platform
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Home ──────────────────────────────────────────
    path('', views.home, name='home'),

    # ── Auth ──────────────────────────────────────────
  

    # ── Products ──────────────────────────────────────
    path('products/',                  views.product_list,   name='product_list'),
    path('products/<slug:slug>/',      views.product_detail, name='product_detail'),
    path('category/<slug:slug>/',      views.category_view,  name='category'),

    # ── Cart ──────────────────────────────────────────
    path('cart/',                           views.cart_view,        name='cart'),
    path('cart/add/<int:product_id>/',      views.add_to_cart,      name='add_to_cart'),
    path('cart/update/<int:item_id>/',      views.update_cart,      name='update_cart'),
    path('cart/remove/<int:item_id>/',      views.remove_from_cart, name='remove_from_cart'),

    # ── Checkout & Orders ─────────────────────────────
    path('checkout/',                         views.checkout,          name='checkout'),
    path('orders/',                           views.order_list,        name='order_list'),
    path('orders/<int:order_id>/',            views.order_detail,      name='order_detail'),
    path('orders/<int:order_id>/confirmed/',  views.order_confirmation, name='order_confirmation'),

    # ── Customer Dashboard ────────────────────────────
    path('dashboard/',         views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/profile/', views.profile_update,     name='profile_update'),

    # ── Wishlist ──────────────────────────────────────
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # ── Vendor Panel ──────────────────────────────────
    path('vendor/',                              views.vendor_dashboard,    name='vendor_dashboard'),
    path('vendor/products/add/',                 views.vendor_add_product,  name='vendor_add_product'),
    path('vendor/products/<int:product_id>/edit/',   views.vendor_edit_product,   name='vendor_edit_product'),
    path('vendor/products/<int:product_id>/delete/', views.vendor_delete_product, name='vendor_delete_product'),

    # ── Admin Panel ───────────────────────────────────
    path('admin-panel/',                              views.admin_dashboard,         name='admin_dashboard'),
    path('admin-panel/users/',                        views.admin_users,             name='admin_users'),
    path('admin-panel/orders/',                       views.admin_orders,            name='admin_orders'),
    path('admin-panel/orders/<int:order_id>/status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/vendors/<int:vendor_id>/approve/', views.admin_approve_vendor, name='admin_approve_vendor'),
]

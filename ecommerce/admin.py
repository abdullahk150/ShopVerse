from django.contrib import admin
from .models import (
    UserProfile, VendorProfile, Category, Product, ProductImage,
    Cart, CartItem, Order, OrderItem, Payment, Review, Wishlist, Address
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'role', 'phone', 'created_at']
    list_filter   = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display  = ['store_name', 'status', 'approved_at']
    list_filter   = ['status']
    search_fields = ['store_name']
    actions       = ['approve_vendors']

    def approve_vendors(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', approved_at=timezone.now(), approved_by=request.user)
    approve_vendors.short_description = "Approve selected vendors"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'parent', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display   = ['name', 'vendor', 'category', 'price', 'stock', 'status']
    list_filter    = ['status', 'category']
    search_fields  = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines        = [ProductImageInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['order_number', 'customer', 'total_amount', 'status', 'created_at']
    list_filter   = ['status']
    search_fields = ['order_number', 'customer__username']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'amount', 'status', 'paid_at']
    list_filter  = ['method', 'status']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'is_verified', 'created_at']
    list_filter  = ['rating', 'is_verified']

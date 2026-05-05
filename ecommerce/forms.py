"""
forms.py - All forms for the E-Commerce Platform
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, VendorProfile, Product, Review, Address, Order


# ─────────────────────────────────────────────
# AUTH FORMS
# ─────────────────────────────────────────────
class CustomerRegistrationForm(UserCreationForm):
    email       = forms.EmailField(required=True)
    first_name  = forms.CharField(max_length=50)
    last_name   = forms.CharField(max_length=50)
    phone       = forms.CharField(max_length=20, required=False)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='customer',
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class VendorRegistrationForm(UserCreationForm):
    email       = forms.EmailField(required=True)
    first_name  = forms.CharField(max_length=50)
    last_name   = forms.CharField(max_length=50)
    store_name  = forms.CharField(max_length=150)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    phone       = forms.CharField(max_length=20, required=False)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile = UserProfile.objects.create(
                user=user,
                role='vendor',
                phone=self.cleaned_data.get('phone', '')
            )
            import re
            slug = re.sub(r'[^\w\s-]', '', self.cleaned_data['store_name']).strip().replace(' ', '-').lower()
            VendorProfile.objects.create(
                user_profile=profile,
                store_name=self.cleaned_data['store_name'],
                store_slug=slug,
                description=self.cleaned_data.get('description', ''),
                status='pending'
            )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name  = forms.CharField(max_length=50)
    email      = forms.EmailField()

    class Meta:
        model  = UserProfile
        fields = ['phone', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial  = self.instance.user.last_name
            self.fields['email'].initial      = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name  = self.cleaned_data['last_name']
        profile.user.email      = self.cleaned_data['email']
        if commit:
            profile.user.save()
            profile.save()
        return profile


# ─────────────────────────────────────────────
# PRODUCT FORM (for vendors)
# ─────────────────────────────────────────────
class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = ['name', 'category', 'description', 'price', 'discount_pct', 'stock', 'sku', 'thumbnail', 'weight_kg', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'discount_pct': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        import re
        self.slug_value = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '-').lower()
        return name

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            product.slug = self.slug_value
        if commit:
            product.save()
        return product


# ─────────────────────────────────────────────
# ADDRESS FORM
# ─────────────────────────────────────────────
class AddressForm(forms.ModelForm):
    class Meta:
        model  = Address
        fields = ['full_name', 'street', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'street': forms.TextInput(attrs={'placeholder': 'House/Flat No., Street, Area'}),
        }


# ─────────────────────────────────────────────
# CHECKOUT FORM
# ─────────────────────────────────────────────
class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod',       'Cash on Delivery'),
        ('easypaisa', 'EasyPaisa'),
    ]

    # Shipping
    full_name    = forms.CharField(max_length=150)
    street       = forms.CharField(max_length=255)
    city         = forms.CharField(max_length=100)
    state        = forms.CharField(max_length=100)
    postal_code  = forms.CharField(max_length=20)
    country      = forms.CharField(max_length=100, initial='Pakistan')
    phone        = forms.CharField(max_length=20, required=False)
    notes        = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    # Payment
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)


# ─────────────────────────────────────────────
# REVIEW FORM
# ─────────────────────────────────────────────
class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect
    )

    class Meta:
        model  = Review
        fields = ['rating', 'title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience…'}),
        }


# ─────────────────────────────────────────────
# PRODUCT SEARCH / FILTER FORM
# ─────────────────────────────────────────────
class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ('',         'Default'),
        ('price_asc','Price: Low to High'),
        ('price_desc','Price: High to Low'),
        ('newest',   'Newest First'),
        ('rating',   'Top Rated'),
    ]

    q           = forms.CharField(required=False, label='Search')
    category    = forms.IntegerField(required=False)
    min_price   = forms.DecimalField(required=False, min_value=0)
    max_price   = forms.DecimalField(required=False, min_value=0)
    sort        = forms.ChoiceField(choices=SORT_CHOICES, required=False)

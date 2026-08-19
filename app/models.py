from decimal import Decimal
from django.db import models
from django.utils.text import slugify
# from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import BaseUserManager,PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# from .managers import CustomUserManager
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.contrib.sites.models import Site





class SiteProfile(models.Model):
    site=models.OneToOneField(Site,on_delete=models.CASCADE,)
    template_name=models.CharField(max_length=100,null=True,blank=True)
    template_address_for_checkout=models.CharField(max_length=100,null=True,blank=True)
    store_name=models.CharField(max_length=100)
    store_logo=models.ImageField(upload_to='store_logos/',null=True,blank=True)
    back_image_at_index=models.ImageField(upload_to='backgrounds/',null=True,blank=True)

    def __str__(self):
        return self.site.domain

class background_image_aat_index_page(models.Model):
    site=models.ForeignKey(Site,on_delete=models.CASCADE,)
    image=models.ImageField(upload_to='backgrounds/',null=True,blank=True)
    main_text=models.CharField(max_length=200,null=True,blank=True)
    sub_text=models.CharField(max_length=200,null=True,blank=True)

    def __str__(self):
        return f"Background for {self.site.domain}"

class Category(models.Model):
    domain = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='categories',null=True,blank=True)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        # Allow multiple categories with same name if they belong to different vendors
        # or if one is global (vendor=None)
        pass
    
    def __str__(self):
        if self.vendor:
            return f"{self.name} ({self.vendor.username})"
        return self.name



class Product(models.Model):
    domain = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='products',null=True,blank=True)
    site=models.ForeignKey(SiteProfile,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products',null=True,blank=True)
    stock_qty = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/',null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.CharField(max_length=100,default='Generic')
    description = models.TextField(default='No description available.')

    has_discount = models.BooleanField(default=False)
    discount_percent = models.PositiveIntegerField(blank=True, null=True)
    discount_start_date = models.DateTimeField(blank=True, null=True)
    discount_end_date = models.DateTimeField(blank=True, null=True)

    @property
    def discount_active(self):
        if not self.discount_start_date or not self.discount_end_date:
            return False
        now = timezone.now()
        return self.has_discount and self.discount_start_date <= now <= self.discount_end_date

    is_new = models.BooleanField(default=False)

    def discounted_price(self):
        if self.has_discount and self.discount_percent:
            return self.price - (self.price * self.discount_percent / 100)
        return self.price

    def __str__(self):
        return self.name


class Cart(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('product','user')

    def __str__(self):
        return f"{self.user.username} | {self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.product.discounted_price()
    
class CartOrder(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)

    def cart_total(self):
        items = Cart.objects.filter(user=self.user)
        return sum(
            (item.subtotal for item in items),
            Decimal('0.00')
        )

    def discount_amount(self):
        if self.coupon and self.coupon.is_valid():
            return self.cart_total() * (self.coupon.discount_percent / Decimal(100))
        return Decimal('0.00')


    def final_total(self):
        return self.cart_total() - self.discount_amount()

    
class Wishlist(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
class Profile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    age=models.PositiveIntegerField(null=True,blank=True)
    picture=models.ImageField(upload_to='profiles/',null=True,blank=True)

    def __str__(self):
        return self.user.username
    




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor',   'Vendor'),
        ('admin',    'Admin'),
    ]

    VENDOR_STATUS_CHOICES = [
        ('not_vendor', 'Not a Vendor'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    email      = models.EmailField(unique=True)
    username   = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    role        = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_approved = models.BooleanField(default=False)  # admin approves vendors (deprecated, use vendor_status)
    
    # New vendor status tracking fields
    vendor_status = models.CharField(max_length=20, choices=VENDOR_STATUS_CHOICES, default='not_vendor')
    vendor_approved_at = models.DateTimeField(null=True, blank=True)
    vendor_approved_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_vendors')
    vendor_rejection_reason = models.TextField(null=True, blank=True)
    vendor_suspended_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def is_admin(self):
        return self.role == 'admin'

    def is_vendor(self):
        return self.role == 'vendor'

    def is_customer(self):
        return self.role == 'customer'

    def is_vendor_approved(self):
        """Check if vendor is approved and can access vendor panel"""
        if self.role != 'vendor':
            return False
        return self.vendor_status == 'approved'

    def is_vendor_pending(self):
        """Check if vendor is awaiting approval"""
        if self.role != 'vendor':
            return False
        return self.vendor_status == 'pending'

    def is_vendor_rejected(self):
        """Check if vendor application was rejected"""
        if self.role != 'vendor':
            return False
        return self.vendor_status == 'rejected'

    def is_vendor_suspended(self):
        """Check if vendor account is suspended"""
        if self.role != 'vendor':
            return False
        return self.vendor_status == 'suspended'

    def can_access_panel(self):
        if self.role == 'admin':
            return True
        if self.role == 'vendor' and self.is_vendor_approved():
            return True
        return False

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def __str__(self):
        return self.code
    

    
class Order(models.Model):

    status_choices = [
        ('pending', 'Pending'),
        ('Done', 'Done'),
        ('Cancelled', 'Cancelled'),
    ]

    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    email=models.EmailField()
    
    address=models.CharField(max_length=250)
    city=models.CharField(max_length=100)
    country=models.CharField(max_length=100,null=True,blank=True)
    zip_code=models.CharField(max_length=20)
    phone=models.CharField(max_length=20)

    total_amount=models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)

    status=models.CharField(max_length=20, choices=status_choices, default='pending')

    

    def __str__(self):
        return f"Order {self.id} by {self.user.email} - {self.status}"


class VendorOrder(models.Model):

    status_choices = [
        ('pending', 'Pending'),
        ('Done', 'Done'),
        ('Cancelled', 'Cancelled'),
    ]

    order=models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_orders')
    vendor=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_orders')
    subtotal=models.DecimalField(max_digits=10, decimal_places=2)
    status=models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vendor Order {self.id} for Order {self.order.id} by Vendor {self.vendor.email} - {self.status}"

    

class OrderItem(models.Model):
    vendor_order=models.ForeignKey(VendorOrder, on_delete=models.CASCADE, related_name='items',null=True,blank=True)
    product=models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    price=models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.price * self.quantity



    

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Vendor Order {self.vendor_order.id}"
    

class booktable(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    email=models.EmailField(max_length=254,null=True,blank=True)
    phone=models.CharField(max_length=20,null=True,blank=True)
    date=models.DateField()
    time=models.TimeField()
    number_of_guests=models.PositiveIntegerField()

    def __str__(self):
        return f"Table booking for {self.name} on {self.date} at {self.time}"

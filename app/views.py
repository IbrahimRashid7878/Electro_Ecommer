import http
from pyexpat.errors import messages
import re
from django import http
from django.contrib.sites.models import Site
from urllib import request
from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.db.models import Count
from app.models import Product, Category
from django.core.paginator import Paginator
# from app.models import Product, Category, Cart ,Wishlist, Profile ,Coupon,CartOrder,Order,OrderItem
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.utils import timezone
from .models import Product, Category, Wishlist,CartOrder,VendorOrder,Coupon,Order,OrderItem,Cart,Profile,SiteProfile,background_image_aat_index_page,booktable
from django.contrib.sites.shortcuts import get_current_site
from app.models import SiteProfile


from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()
now = timezone.now()

def current_site_profile(request):
    site=get_current_site(request)
    # current_domain = request.get_host()
    
    site_profile=SiteProfile.objects.get(site=site)
    return {'site_profile': site_profile}

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Last Name'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email'})


# Create your views here.

def shop(request):
    
    current_site=get_current_site(request)
    site_profile=SiteProfile.objects.get(site=current_site)


    products = Product.objects.filter(site=site_profile)
    categories = Category.objects.filter(domain=site_profile)

    companies = (Product.objects.values('company').annotate(count=Count('id')))

    category_name = request.GET.get('category', "").strip()
    if category_name and category_name.lower() != "all":
        products = products.filter(category__name=category_name)

    selected_categories = request.GET.getlist('category')
    if selected_categories:
        products = products.filter(category__name__in=selected_categories)

    selected_companies = request.GET.getlist('company')
    if selected_companies:
        products = products.filter(company__in=selected_companies)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)


    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(company__icontains=query)
        )
    
    



    page_details=Paginator(products, 3)
    page_number=request.GET.get('page')
    final_page=page_details.get_page(page_number)

    querey_dict=request.GET.copy()
    querey_dict.pop('page', None)
    querey_string=urlencode(querey_dict, doseq=True)


    


    return render(request, 'store.html', {
        'products': final_page,
        'categories': categories,
        'selected_categories': selected_categories,
        'companies': companies, 
        'selected_companies': selected_companies,
        'min_price': min_price,
        'max_price': max_price,
        'querey_string': querey_string,
        'query': query,
        # 'products':products,
        'cart_count': get_cart_count(request),
        'wishlist_count': get_wishlist_count(request)

    })

def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist_item.delete()

    else:

        wishlist = request.session.get('wishlist', [])

        if product_id in wishlist:
            wishlist.remove(product_id)
        else:
            wishlist.append(product_id)

        request.session['wishlist'] = wishlist

    return redirect(request.META.get('HTTP_REFERER', 'shop'))


def remove_from_wishlist(request, product_id):
    product_id = int(product_id)

    if request.user.is_authenticated:
        Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    else:
        wishlist = request.session.get('wishlist', [])
        if product_id in wishlist:
            wishlist.remove(product_id)
            request.session['wishlist'] = wishlist

    return redirect('wishlist')

def wishlist_view(request):
    if request.user.is_authenticated:
       items = [w.product for w in Wishlist.objects.filter(user=request.user)]
    else:
        wishlist = request.session.get('wishlist', [])
        wishlist = [int(pid) for pid in wishlist]
        items = Product.objects.filter(id__in=wishlist)

    return render(request, 'wishlist.html', {
        'items': items,
        'cart_count': get_cart_count(request),
        'wishlist_count': get_wishlist_count(request)
    })

def get_wishlist_count(request):
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).count()
    else:
        wishlist = request.session.get('wishlist', [])
        return len(wishlist)

def quick_view(request):
    product_id = request.GET.get('id')
    product = Product.objects.get(id=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'category': product.category.name,
        'company': product.company,
        'price': float(product.discounted_price() if product.has_discount else product.price),
        'description': product.description,
        'image': product.image.url,
        'cart_count': get_cart_count(request),
        'wishlist_count': get_wishlist_count(request)
    })

import urllib.parse


def product(request):
    product_id = request.GET.get('id')
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'product.html', {
        'product': product,
        'cart_count': get_cart_count(request),
        'wishlist_count': get_wishlist_count(request)
    })


def send_whatsapp_message(request):
    product_id = request.GET.get('id')
    product = get_object_or_404(Product, id=product_id)

    phone_number = "923129675178"

    message = f"""
                Hello, I am interested in your product:

                Product Name: {product.name}
                Price: Rs {product.price}

                Is it available?
                What are the delivery charges?
                """

    encoded_message = urllib.parse.quote(message)

    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
    return redirect(whatsapp_url)



# from twilio.rest import Client
# from django.http import HttpResponse


# def send_buttons(request):
#     from twilio.rest import Client
#     from .models import Product

#     product_id = request.GET.get('id')
#     product = Product.objects.get(id=product_id)

#     client = Client('AC6b7953e24d9e49be58aa69b6457359da', 'd5a8454a56a4fa25b106ac71046c06fb')

#     message = client.messages.create(
#         from_='whatsapp:+14155238886',
#         to='whatsapp:+923129675178',
#         content_sid='HXd77a995988e23d882b74d09c51cc96a9'
#     )

#     return HttpResponse("Message Sent!")

# from django.views.decorators.csrf import csrf_exempt
# from django.http import HttpResponse

# @csrf_exempt
# def whatsapp_webhook(request):
#     incoming_msg = request.POST.get('Body', '').strip().lower()

#     if incoming_msg == '1':
#         reply = "Yes, product is available "
#     elif incoming_msg == '2':
#         reply = "Delivery is Rs 200 "
#     elif incoming_msg == '3':
#         reply = "Send your address to place order "
#     else:
#         reply = "Reply with:\n1. Availability\n2. Delivery\n3. Order"

#     from twilio.twiml.messaging_response import MessagingResponse
#     resp = MessagingResponse()
#     resp.message(reply)

#     return HttpResponse(str(resp))

def index(request):
    current_site=get_current_site(request)
    site_profile=SiteProfile.objects.get(site=current_site)
    products=Product.objects.filter(site=site_profile)
    category=Category.objects.filter(domain=site_profile)
    background=background_image_aat_index_page.objects.filter(site=current_site)


    return render(request, site_profile.template_name, {'products': products,'wishlist_count': get_wishlist_count(request),'category': category,'site_profile': site_profile,'background': background,'cart_count': get_cart_count(request)})
        

# def checkout(request):
#     return render(request, 'checkout.html')

def blank(request):
    return render(request, 'blank.html')

def categories(request):
    categories=Category.objects.all()
    return render(request, 'categories.html', {'categories': categories,'cart_count': get_cart_count(request), 'wishlist_count': get_wishlist_count(request)})

def cart(request):
    items = Cart.objects.filter(user=request.user)
    cart_order, created = CartOrder.objects.get_or_create(
        user=request.user
    )
    message = None
    if request.method == "POST":
        code = request.POST.get("coupon_code", "").strip()
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.is_valid():
                cart_order.coupon = coupon
                cart_order.save()
                message = "Coupon applied on total amount"
            else:
                message = "Coupon expired or not active"
        except Coupon.DoesNotExist:
            message = "Invalid coupon code entered"
    return render(request, 'cart.html', {
        'cart_items': items,
        'cart_total': cart_order.cart_total(),
        'discount': cart_order.discount_amount(),
        'final_total': cart_order.final_total(),
        'message': message,
        'cart_count': get_cart_count(request),
        'wishlist_count': get_wishlist_count(request)
    })

def get_cart_count(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).count()
    return 0

@login_required(login_url='login')
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

    

    return redirect(request.META.get('HTTP_REFERER', 'shop'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(Cart, id=item_id)
    item.quantity -= 1
    if item.quantity <= 0:
        item.delete()
    else:
        item.save()
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(Cart, id=item_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart')

from collections import defaultdict
from django.db import transaction

@login_required
def checkout(request):
    current_site=get_current_site(request)
    site_profile=SiteProfile.objects.get(site=current_site)





    cart_items = Cart.objects.filter(user=request.user).select_related(
        'product',
        'product__vendor'
    )

    cart_order, created = CartOrder.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        if not cart_items.exists():
            from django.contrib import messages as flash
            flash.error(request, "Your cart is empty.")
            return redirect('cart')

        vendor_items = defaultdict(list)

        for item in cart_items:

            if not item.product.vendor:
                from django.contrib import messages as flash
                flash.error(
                    request,
                    f"Product '{item.product.name}' has no vendor assigned."
                )
                return redirect('cart')

            vendor_items[item.product.vendor].append(item)

        with transaction.atomic():

            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
                email=request.POST.get("email"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                country=request.POST.get("country"),
                zip_code=request.POST.get("zip_code"),
                phone=request.POST.get("phone"),
                total_amount=cart_order.final_total()
            )

            for vendor, items in vendor_items.items():

                subtotal = sum(
                    (
                        item.product.discounted_price()
                        if item.product.discount_active
                        else item.product.price
                    ) * item.quantity
                    for item in items
                )

                vendor_order = VendorOrder.objects.create(
                    order=order,
                    vendor=vendor,
                    subtotal=subtotal,
                    status='pending'
                )

                for item in items:

                    product_price = (
                        item.product.discounted_price()
                        if item.product.discount_active
                        else item.product.price
                    )

                    OrderItem.objects.create(
                        vendor_order=vendor_order,
                        product=item.product,
                        quantity=item.quantity,
                        price=product_price
                    )

            cart_items.delete()

            cart_order.coupon = None
            cart_order.save()

        items_list = "\n".join([
            f"{vendor_order.vendor.username}: "
            + ", ".join(
                f"{item.product.name} x {item.quantity}"
                for item in vendor_order.items.all()
            )
            for vendor_order in order.vendor_orders.all()
        ])

        email_message = f"""Dear {order.first_name},

Your order #{order.id} has been received.

Items:
{items_list}

Total amount: Rs {order.total_amount}

Thank you for your order.

Best regards,
The Team"""

        send_mail(
            "Order Confirmation",
            email_message,
            settings.EMAIL_HOST_USER,
            [order.email],
            fail_silently=False
        )

        return redirect('index')

    return render(request, 'checkout.html', {
        "cart_items": cart_items,
        'final_total': cart_order.final_total(),
        'cart_total': cart_order.cart_total(),
        'wishlist_count': get_wishlist_count(request),
        'cart_count': get_cart_count(request)
    })
        
    
    



def register(request):
    
    form = CustomUserCreationForm(request.POST or None,request.FILES or None)
    

    if request.method=='POST' and form.is_valid():
        user=form.save()

        

        Profile.objects.create(
            user=user,
            age=request.POST.get("age")or None,
            picture=request.FILES.get('picture') or None)  

        return redirect('login')
    return render(request, 'register.html', {'form': form})



@login_required
def account(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    

    return render(request,'account.html')


 
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
)
from django.db.models import Sum
 
 
 
def panel_login(request):
    """
    Panel login view that routes users based on role and vendor status.
    Prevents unapproved/rejected/suspended vendors from accessing the panel.
    """
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'vendor':
            if request.user.vendor_status == 'approved':
                return redirect('vendor_dashboard')
            elif request.user.vendor_status == 'pending':
                from django.contrib import messages as flash
                flash.warning(request, 'Your vendor account is pending admin approval. Please wait.')
                return render(request, 'custom_admin_templates/login.html', {'status': 'pending'})
            elif request.user.vendor_status == 'rejected':
                from django.contrib import messages as flash
                reason = request.user.vendor_rejection_reason or 'No reason provided.'
                flash.error(request, f'Your vendor application was rejected. Reason: {reason}')
                return render(request, 'custom_admin_templates/login.html', {'status': 'rejected'})
            elif request.user.vendor_status == 'suspended':
                from django.contrib import messages as flash
                flash.error(request, 'Your vendor account is suspended. Please contact admin.')
                return render(request, 'custom_admin_templates/login.html', {'status': 'suspended'})
        return redirect('shop')
 
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        user     = authenticate(request, username=email, password=password)
 
        if user:
            if user.role == 'customer':
                from django.contrib import messages as flash
                flash.error(request, 'Customers cannot access the panel.')
                return redirect('shop')
            
            # Check vendor status before login
            if user.role == 'vendor':
                if user.vendor_status == 'pending':
                    from django.contrib import messages as flash
                    flash.warning(request, 'Your vendor account is pending admin approval. Please wait for approval.')
                    return render(request, 'custom_admin_templates/login.html', {'status': 'pending'})
                elif user.vendor_status == 'rejected':
                    from django.contrib import messages as flash
                    reason = user.vendor_rejection_reason or 'No reason provided.'
                    flash.error(request, f'Your vendor application was rejected. Reason: {reason}')
                    return render(request, 'custom_admin_templates/login.html', {'status': 'rejected'})
                elif user.vendor_status == 'suspended':
                    from django.contrib import messages as flash
                    flash.error(request, 'Your vendor account is suspended. Please contact the administrator.')
                    return render(request, 'custom_admin_templates/login.html', {'status': 'suspended'})
                elif user.vendor_status != 'approved':
                    from django.contrib import messages as flash
                    flash.error(request, 'Your vendor account status is invalid. Please contact admin.')
                    return render(request, 'custom_admin_templates/login.html')
            
            auth_login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('vendor_dashboard')
        else:
            from django.contrib import messages as flash
            flash.error(request, 'Wrong email or password.')
 
    return render(request, 'custom_admin_templates/login.html')
 
 
 
def panel_logout(request):
    auth_logout(request)
    return redirect('panel_login')


def vendor_customers(request):
    """
    View customers who have purchased from the logged-in vendor.
    Each vendor only sees customers relevant to their own products/orders.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')

    if request.user.role == 'customer':
        return redirect('shop')

    if request.user.role == 'vendor':
        # Vendor approval check
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        
        # Get unique customers who have ordered this vendor's products
        # Query: Customer -> Order -> VendorOrder -> Vendor
        customers = User.objects.filter(
            # The customer's orders must contain VendorOrders from this vendor
            order__vendor_orders__vendor=request.user,
            role='customer'  # Only actual customers
        ).distinct().prefetch_related(
            'order_set'  # For displaying their order info
        )
    else:
        # Admin sees all customers
        customers = User.objects.filter(role='customer').prefetch_related('order_set')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'custom_admin_templates/vendor_customers.html', {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
    })


def vendor_dashboard(request):
    """
    Vendor and admin dashboard view.
    Vendors must be approved to access, admins have full access.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    
    if request.user.role == 'customer':
        from django.contrib import messages as flash
        flash.error(request, 'Customers cannot access the vendor panel.')
        return redirect('shop')
    
    if request.user.role == 'vendor':
        # Check vendor approval status
        if request.user.vendor_status == 'pending':
            from django.contrib import messages as flash
            flash.warning(request, 'Your vendor account is pending admin approval.')
            return redirect('panel_login')
        elif request.user.vendor_status == 'rejected':
            from django.contrib import messages as flash
            flash.error(request, 'Your vendor application was rejected.')
            return redirect('panel_login')
        elif request.user.vendor_status == 'suspended':
            from django.contrib import messages as flash
            flash.error(request, 'Your vendor account is suspended.')
            return redirect('panel_login')
        elif request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'Your vendor account status is invalid.')
            return redirect('panel_login')
        
        # Approved vendor - show their data
        products = Product.objects.filter(vendor=request.user).select_related('category')
        orders = VendorOrder.objects.filter(vendor=request.user).select_related('order').order_by('-created_at')[:10]
        
        total_revenue = VendorOrder.objects.filter(
            vendor=request.user, status='Done'
        ).aggregate(total=Sum('subtotal'))['total'] or 0
    else:
        # Admin - show all data
        products = Product.objects.all().select_related('vendor', 'category')
        orders = VendorOrder.objects.all().select_related('order', 'vendor').order_by('-created_at')[:10]
        
        total_revenue = VendorOrder.objects.filter(
            status='Done'
        ).aggregate(total=Sum('subtotal'))['total'] or 0
 
    return render(request, 'custom_admin_templates/vendor_dashboard.html', {
        'products':      products,
        'orders':        orders,
        'total_revenue': total_revenue,
        'product_count': products.count(),
        'order_count':   orders.count(),
    })
 
 
 
def vendor_orders(request):

    if not request.user.is_authenticated:
        return redirect('panel_login')

    if request.user.role == 'customer':
        return redirect('shop')

    if request.user.role == 'vendor' and not request.user.is_approved:
        return redirect('panel_login')

    status_filter = request.GET.get('status', '').strip()

    if request.user.role == 'admin':
        orders = VendorOrder.objects.all()
    else:
        orders = VendorOrder.objects.filter(
            vendor=request.user
        )

    orders = orders.order_by('-created_at')

    valid_statuses = [
        'pending',
        'processing',
        'shipped',
        'done',
        'cancelled',
    ]

    if status_filter in valid_statuses:
        orders = orders.filter(status=status_filter)

  
    if request.user.role == 'admin':
        all_orders = VendorOrder.objects.all()
    else:
        all_orders = VendorOrder.objects.filter(
            vendor=request.user
        )

    return render(
        request,
        'custom_admin_templates/vendor_orders.html',
        {
            'orders': orders,
            'status_filter': status_filter,

            'total_count': all_orders.count(),
            'pending_count': all_orders.filter(status='pending').count(),
            'processing_count': all_orders.filter(status='processing').count(),
            'shipped_count': all_orders.filter(status='shipped').count(),
            'done_count': all_orders.filter(status='done').count(),
            'cancelled_count': all_orders.filter(status='cancelled').count(),
        }
    )
 
def order_detail(request, order_id):

    if not request.user.is_authenticated:
        return redirect('panel_login')

    if request.user.role == 'customer':
        return redirect('shop')

    order = get_object_or_404(
        VendorOrder.objects.select_related(
            'order',
            'vendor',
            'order__user'
        ),
        id=order_id
    )

    if (
        request.user.role == 'vendor'
        and order.vendor != request.user
    ):
        from django.contrib import messages as flash
        flash.error(
            request,
            "You do not have permission to view this order."
        )
        return redirect('vendor_orders')

    items = order.items.select_related('product')

    return render(
        request,
        'custom_admin_templates/order_detail.html',
        {
            'vendor_order': order,
            'order': order.order,
            'items': items,
        }
    )
 
 
 
def my_products(request):
    """
    View products - admins see all, vendors see only their own.
    Vendors must be approved to access.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        from django.contrib import messages as flash
        flash.error(request, 'Customers cannot access this page.')
        return redirect('shop')

    if request.user.role == 'vendor':
        # Check vendor approval status
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        products = Product.objects.filter(vendor=request.user).select_related('category')
    else:
        # Admin sees all
        products = Product.objects.all().select_related('vendor', 'category')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
 
    return render(request, 'custom_admin_templates/products.html', {
        'page_obj': page_obj,
        'products': page_obj.object_list,
    })
 
 
 
def product_add(request):
    """
    Add a new product - only approved vendors and admins.
    Vendor is automatically assigned to the authenticated user.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        from django.contrib import messages as flash
        flash.error(request, 'Customers cannot add products.')
        return redirect('shop')
    
    if request.user.role == 'vendor':
        # Check vendor approval status
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to add products.')
            return redirect('panel_login')
        # Vendors see only their own categories
        categories = Category.objects.filter(vendor=request.user)
    else:
        # Admins see all categories
        categories = Category.objects.all()
 
    if request.method == 'POST':
        try:
            current_site = get_current_site(request)
            site_profile = SiteProfile.objects.get(site=current_site)
            category = Category.objects.get(id=request.POST.get('category'))
            
            # Vendor can only use their own categories
            if request.user.role == 'vendor' and category.vendor != request.user:
                from django.contrib import messages as flash
                flash.error(request, 'You can only use your own categories.')
                return render(request, 'custom_admin_templates/Add_product.html', {
                    'categories': categories
                })
            
            # For vendors, automatically set vendor to self
            # For admins, allow selecting vendor (optional - currently auto-set)
            vendor = request.user if request.user.role == 'vendor' else request.user
            
            Product.objects.create(
                domain              = site_profile,
                site                = site_profile,
                name                = request.POST.get('name'),
                category            = category,
                vendor              = vendor,
                price               = request.POST.get('price'),
                stock_qty           = request.POST.get('stock_qty', 0),
                company             = request.POST.get('company', 'Generic'),
                description         = request.POST.get('description', ''),
                image               = request.FILES.get('image'),
                is_new              = bool(request.POST.get('is_new')),
                has_discount        = bool(request.POST.get('has_discount')),
                discount_percent    = request.POST.get('discount_percent') or None,
                discount_start_date = request.POST.get('discount_start_date') or None,
                discount_end_date   = request.POST.get('discount_end_date') or None,
            )
            from django.contrib import messages as flash
            flash.success(request, 'Product added successfully.')
            return redirect('my_products')
        except Exception as e:
            from django.contrib import messages as flash
            flash.error(request, f'Error adding product: {str(e)}')
 
    return render(request, 'custom_admin_templates/Add_product.html', {
        'categories': categories
    })
 
 
 
def panel_product_detail(request, product_id):
    """
    View and edit product details - only vendor owner or admin can edit.
    Vendor must be approved.
    IDOR protection: vendors can only edit their own products.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        from django.contrib import messages as flash
        flash.error(request, 'Customers cannot edit products.')
        return redirect('shop')
 
    product = get_object_or_404(Product, id=product_id)

    # Authorization check - IDOR protection
    if request.user.role == 'vendor':
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'Your vendor account is not approved.')
            return redirect('my_products')
        
        if product.vendor != request.user:
            from django.contrib import messages as flash
            flash.error(request, 'You do not have permission to edit this product.')
            return redirect('my_products')

    categories = Category.objects.all()
 
    if request.method == 'POST':
        try:
            product.name                = request.POST.get('name')
            product.price               = request.POST.get('price')
            product.stock_qty           = request.POST.get('stock_qty', 0)
            product.company             = request.POST.get('company', 'Generic')
            product.description         = request.POST.get('description', '')
            product.category            = Category.objects.get(id=request.POST.get('category'))
            product.is_new              = bool(request.POST.get('is_new'))
            product.has_discount        = bool(request.POST.get('has_discount'))
            product.discount_percent    = request.POST.get('discount_percent') or None
            product.discount_start_date = request.POST.get('discount_start_date') or None
            product.discount_end_date   = request.POST.get('discount_end_date') or None
     
            if request.FILES.get('image'):
                product.image = request.FILES.get('image')
     
            product.save()
            from django.contrib import messages as flash
            flash.success(request, 'Product updated successfully.')
            return redirect('panel_product_detail', product_id=product.id)
        except Exception as e:
            from django.contrib import messages as flash
            flash.error(request, f'Error updating product: {str(e)}')
 
    return render(request, 'custom_admin_templates/product_detail.html', {
        'product':    product,
        'categories': categories,
    })
 
 
 
def product_delete(request, product_id):
    """
    Delete a product - only vendor owner or admin can delete.
    Uses POST method for safety.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        from django.contrib import messages as flash
        flash.error(request, 'Customers cannot delete products.')
        return redirect('shop')
 
    product = get_object_or_404(Product, id=product_id)

    # Authorization check - IDOR protection
    if request.user.role == 'vendor':
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'Your vendor account is not approved.')
            return redirect('my_products')
        
        if product.vendor != request.user:
            from django.contrib import messages as flash
            flash.error(request, 'You do not have permission to delete this product.')
            return redirect('my_products')
 
    if request.method == 'POST':
        try:
            product.delete()
            from django.contrib import messages as flash
            flash.success(request, 'Product deleted successfully.')
        except Exception as e:
            from django.contrib import messages as flash
            flash.error(request, f'Error deleting product: {str(e)}')
 
    return redirect('my_products')
 
 
 
def admin_dashboard(request):
    """
    Admin dashboard view showing system-wide statistics.
    Only accessible to admins.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to access this resource.')
        return redirect('vendor_dashboard')
 
    today = timezone.now().date()
 
    # Get vendor status counts
    all_vendors = User.objects.filter(role='vendor')
    
    stats = {
        'total_users':      User.objects.count(),
        'vendor_count':     all_vendors.count(),
        'pending_vendors':  all_vendors.filter(vendor_status='pending').count(),
        'approved_vendors': all_vendors.filter(vendor_status='approved').count(),
        'rejected_vendors': all_vendors.filter(vendor_status='rejected').count(),
        'suspended_vendors':all_vendors.filter(vendor_status='suspended').count(),
        'product_count':    Product.objects.count(),
        'orders_today':     Order.objects.filter(created_at__date=today).count(),
        'revenue_today':    Order.objects.filter(
                                created_at__date=today, status='Done'
                              ).aggregate(t=Sum('total_amount'))['t'] or 0,
    }
 
    pending_vendors = User.objects.filter(role='vendor', vendor_status='pending').select_related()
    recent_orders   = Order.objects.all().select_related('user').order_by('-created_at')[:10]
 
    return render(request, 'custom_admin_templates/admin_dashboard.html', {
        'stats':           stats,
        'pending_vendors': pending_vendors,
        'recent_orders':   recent_orders,
    })
 
 
 
def manage_vendors(request):
    """
    Admin page to view and manage vendors.
    Shows vendors by status (pending, approved, rejected, suspended).
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to access this resource.')
        return redirect('vendor_dashboard')
    
    # Get filter from query params
    status_filter = request.GET.get('status', '').strip()
    valid_statuses = ['pending', 'approved', 'rejected', 'suspended', 'all']
    
    vendors = User.objects.filter(role='vendor').select_related('vendor_approved_by')
    
    if status_filter in valid_statuses and status_filter != 'all':
        vendors = vendors.filter(vendor_status=status_filter)
    
    vendors = vendors.order_by('-last_login')
 
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(vendors, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'custom_admin_templates/manage_vendors.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_counts': {
            'pending': User.objects.filter(role='vendor', vendor_status='pending').count(),
            'approved': User.objects.filter(role='vendor', vendor_status='approved').count(),
            'rejected': User.objects.filter(role='vendor', vendor_status='rejected').count(),
            'suspended': User.objects.filter(role='vendor', vendor_status='suspended').count(),
        }
    })
 
 
def approve_vendor(request, user_id):
    """
    Admin action to approve a vendor.
    Only works with POST requests for safety.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to perform this action.')
        return redirect('vendor_dashboard')
 
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        if vendor.vendor_status == 'approved':
            from django.contrib import messages as flash
            flash.warning(request, f'{vendor.username} is already approved.')
        else:
            vendor.vendor_status = 'approved'
            vendor.vendor_approved_at = timezone.now()
            vendor.vendor_approved_by = request.user
            vendor.is_approved = True  # Keep for backward compatibility
            vendor.save()
            
            from django.contrib import messages as flash
            flash.success(request, f'{vendor.username} has been approved.')
    
    return redirect('manage_vendors')


def reject_vendor(request, user_id):
    """
    Admin action to reject a vendor application.
    Only works with POST requests for safety.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to perform this action.')
        return redirect('vendor_dashboard')
 
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        if vendor.vendor_status == 'rejected':
            from django.contrib import messages as flash
            flash.warning(request, f'{vendor.username} is already rejected.')
        else:
            reason = request.POST.get('reason', 'No reason provided.').strip()
            vendor.vendor_status = 'rejected'
            vendor.vendor_rejection_reason = reason
            vendor.is_approved = False
            vendor.save()
            
            from django.contrib import messages as flash
            flash.success(request, f'{vendor.username} application has been rejected.')
    
    return redirect('manage_vendors')


def suspend_vendor(request, user_id):
    """
    Admin action to suspend a vendor account.
    Only works with POST requests for safety.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to perform this action.')
        return redirect('vendor_dashboard')
 
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        if vendor.vendor_status == 'suspended':
            from django.contrib import messages as flash
            flash.warning(request, f'{vendor.username} is already suspended.')
        else:
            vendor.vendor_status = 'suspended'
            vendor.vendor_suspended_at = timezone.now()
            vendor.save()
            
            from django.contrib import messages as flash
            flash.success(request, f'{vendor.username} account has been suspended.')
    
    return redirect('manage_vendors')


def reactivate_vendor(request, user_id):
    """
    Admin action to reactivate a rejected or suspended vendor.
    Sets vendor back to pending status.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to perform this action.')
        return redirect('vendor_dashboard')
 
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        if vendor.vendor_status == 'pending':
            from django.contrib import messages as flash
            flash.warning(request, f'{vendor.username} is already pending.')
        else:
            vendor.vendor_status = 'pending'
            vendor.vendor_rejection_reason = None
            vendor.vendor_suspended_at = None
            vendor.save()
            
            from django.contrib import messages as flash
            flash.success(request, f'{vendor.username} can now reapply.')
    
    return redirect('manage_vendors')
 
 
def ban_user(request, user_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        from django.contrib import messages as flash
        flash.error(request, 'You do not have permission to perform this action.')
        return redirect('vendor_dashboard')
 
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.is_active = False
        user.save()
        from django.contrib import messages as flash
        flash.success(request, f'{user.username} has been banned.')
    return redirect('manage_vendors')
 
 
 
def manage_users(request):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        return redirect('vendor_dashboard')
 
    users = User.objects.all().order_by('-last_login')
 
    return render(request, 'custom_admin_templates/manage_users.html', {
        'users': users
    })
 
 
def unban_user(request, user_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        return redirect('vendor_dashboard')
 
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.is_active = True
        user.save()
        from django.contrib import messages as flash
        flash.success(request, f'{user.username} unbanned.')
    return redirect('manage_users')
 
 
def change_user_role(request, user_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'admin':
        return redirect('vendor_dashboard')
 
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ('customer', 'vendor', 'admin'):
            user.role = new_role
            if new_role != 'vendor':
                user.is_approved = False
            user.save()
            from django.contrib import messages as flash
            flash.success(request, f'Role changed to {new_role}.')
    return redirect('manage_users')
 
 
 
 

def manage_categories(request):
    """
    Manage categories - vendors see only their own, admins see all.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        return redirect('shop')

    if request.user.role == 'vendor':
        # Vendor approval check
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        # Show only this vendor's categories
        categories = Category.objects.filter(vendor=request.user).order_by('name')
    else:
        # Admin sees all categories (including global ones and all vendor categories)
        categories = Category.objects.all().order_by('name')

    return render(request, 'custom_admin_templates/manage_categories.html', {
        'categories': categories
    })


def category_add(request):
    """
    Add a new category - vendors create their own, admins can create global/any.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        return redirect('shop')

    if request.user.role == 'vendor':
        # Vendor approval check
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            current_site = get_current_site(request)
            site_profile = SiteProfile.objects.get(site=current_site)
            
            # Vendors create categories for themselves, admins can choose
            if request.user.role == 'vendor':
                vendor = request.user
            else:
                vendor = None  # Admin can create global categories
            
            Category.objects.create(
                name=name, 
                domain=site_profile,
                vendor=vendor
            )
            from django.contrib import messages as flash
            flash.success(request, f'Category "{name}" added.')
            return redirect('manage_categories')
        else:
            from django.contrib import messages as flash
            flash.error(request, 'Category name cannot be empty.')

    return render(request, 'custom_admin_templates/categories_add.html')


def category_edit(request, category_id):
    """
    Edit a category - vendors can only edit their own categories.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        return redirect('shop')

    category = get_object_or_404(Category, id=category_id)
    
    # Vendor can only edit their own categories
    if request.user.role == 'vendor':
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        if category.vendor != request.user:
            from django.contrib import messages as flash
            flash.error(request, 'You can only edit your own categories.')
            return redirect('manage_categories')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            category.name = name
            category.save()
            from django.contrib import messages as flash
            flash.success(request, f'Category updated to "{name}".')
            return redirect('manage_categories')
        else:
            from django.contrib import messages as flash
            flash.error(request, 'Category name cannot be empty.')

    return render(request, 'custom_admin_templates/categories_edit.html', {
        'category': category
    })


def category_delete(request, category_id):
    """
    Delete a category - vendors can only delete their own.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        return redirect('shop')

    category = get_object_or_404(Category, id=category_id)
    
    # Vendor can only delete their own categories
    if request.user.role == 'vendor':
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        if category.vendor != request.user:
            from django.contrib import messages as flash
            flash.error(request, 'You can only delete your own categories.')
            return redirect('manage_categories')

    if request.method == 'POST':
        category.delete()
        from django.contrib import messages as flash
        flash.success(request, 'Category deleted.')

    return redirect('manage_categories')



def view_carts(request):
    """
    View shopping carts - vendors see only items with their products.
    Admins see all carts.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role == 'customer':
        return redirect('shop')

    if request.user.role == 'vendor':
        # Vendor approval check
        if request.user.vendor_status != 'approved':
            from django.contrib import messages as flash
            flash.error(request, 'You must be an approved vendor to access this page.')
            return redirect('panel_login')
        
        # Get only cart items with this vendor's products
        cart_items = Cart.objects.filter(
            product__vendor=request.user
        ).select_related('user', 'product').order_by('user__username')
    else:
        # Admin sees all cart items
        cart_items = Cart.objects.select_related('user', 'product').order_by('user__username')

    # Group by user
    from collections import defaultdict
    carts_by_user = defaultdict(list)
    for item in cart_items:
        carts_by_user[item.user].append(item)

    # Build cart data
    cart_data = []
    for user, items in carts_by_user.items():
        total = sum(item.subtotal for item in items)
        cart_data.append({
            'user':  user,
            'items': items,
            'total': total,
            'count': len(items),  
        })

    return render(request, 'custom_admin_templates/view_carts.html', {
        'cart_data':   cart_data,
        'total_carts': len(cart_data),  
    })



def manage_coupons(request):
    """
    Manage coupons - only approved vendors can create/edit coupons.
    """
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'vendor':
        return redirect('vendor_dashboard')
    
    if request.user.vendor_status != 'approved':
        from django.contrib import messages as flash
        flash.error(request, 'You must be an approved vendor to manage coupons.')
        return redirect('panel_login')

    coupons = Coupon.objects.all().order_by('-valid_from')

    return render(request, 'custom_admin_templates/manage_coupons.html', {
        'coupons': coupons
    })


def coupon_add(request):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'vendor':
        return redirect('vendor_dashboard')

    if request.method == 'POST':
        code             = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent')
        valid_from       = request.POST.get('valid_from')
        valid_to         = request.POST.get('valid_to')
        active           = bool(request.POST.get('active'))

        if Coupon.objects.filter(code=code).exists():
            from django.contrib import messages as flash
            flash.error(request, f'Coupon code "{code}" already exists.')
            return render(request, 'custom_admin_templates/coupon_add.html')

        Coupon.objects.create(
            code             = code,
            discount_percent = discount_percent,
            valid_from       = valid_from,
            valid_to         = valid_to,
            active           = active,
        )
        from django.contrib import messages as flash
        flash.success(request, f'Coupon "{code}" created.')
        return redirect('manage_coupons')

    return render(request, 'custom_admin_templates/coupons_add.html')


def coupon_edit(request, coupon_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'vendor':
        return redirect('vendor_dashboard')

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        code             = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent')
        valid_from       = request.POST.get('valid_from')
        valid_to         = request.POST.get('valid_to')
        active           = bool(request.POST.get('active'))

        if Coupon.objects.filter(code=code).exclude(id=coupon.id).exists():
            from django.contrib import messages as flash
            flash.error(request, f'Coupon code "{code}" already exists.')
            return render(request, 'custom_admin_templates/coupons_edit.html', {
                'coupon': coupon
            })

        coupon.code             = code
        coupon.discount_percent = discount_percent
        coupon.valid_from       = valid_from
        coupon.valid_to         = valid_to
        coupon.active           = active
        coupon.save()

        from django.contrib import messages as flash
        flash.success(request, f'Coupon "{code}" updated.')
        return redirect('manage_coupons')

    return render(request, 'custom_admin_templates/coupons_edit.html', {
        'coupon': coupon
    })


def coupon_delete(request, coupon_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'vendor':
        return redirect('vendor_dashboard')

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        from django.contrib import messages as flash
        flash.success(request, f'Coupon "{code}" deleted.')

    return redirect('manage_coupons')


def coupon_toggle(request, coupon_id):
    if not request.user.is_authenticated:
        return redirect('panel_login')
    if request.user.role != 'vendor':
        return redirect('vendor_dashboard')

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        coupon.active = not coupon.active
        coupon.save()
        status = 'activated' if coupon.active else 'deactivated'
        from django.contrib import messages as flash
        flash.success(request, f'Coupon "{coupon.code}" {status}.')

    return redirect('manage_coupons')



# def vendor_orders(request):
#     if not request.user.is_authenticated:
#         return redirect('panel_login')
#     if request.user.role == 'customer':
#         return redirect('shop')

#     status_filter = request.GET.get('status', '').strip()

#     orders = Order.objects.all().order_by('-created_at')

#     if status_filter in ('pending', 'Done', 'Cancelled'):
#         orders = orders.filter(status=status_filter)

#     total_count     = Order.objects.count()
#     pending_count   = Order.objects.filter(status='pending').count()
#     done_count      = Order.objects.filter(status='Done').count()
#     cancelled_count = Order.objects.filter(status='Cancelled').count()

#     return render(request, 'custom_admin_templates/vendor_orders.html', {
#         'orders':          orders,
#         'status_filter':   status_filter,
#         'total_count':     total_count,
#         'pending_count':   pending_count,
#         'done_count':      done_count,
#         'cancelled_count': cancelled_count,
#     })


@login_required
def all_orders(request):

    if request.user.role != 'admin':
        return redirect('vendor_dashboard')

    status_filter = request.GET.get('status', '').strip()

    orders = Order.objects.all().order_by('-created_at')

    if status_filter in ('pending', 'Done', 'Cancelled'):
        orders = orders.filter(status=status_filter)

    total_count = Order.objects.count()
    pending_count = Order.objects.filter(status='pending').count()
    done_count = Order.objects.filter(status='Done').count()
    cancelled_count = Order.objects.filter(status='Cancelled').count()

    return render(request, 'custom_admin_templates/all_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'done_count': done_count,
        'cancelled_count': cancelled_count,
    })


@login_required
def all_order_detail(request, order_id):

    if request.user.role != 'admin':
        return redirect('vendor_dashboard')

    order = get_object_or_404(
        Order.objects.prefetch_related(
            'vendor_orders__items__product',
            'vendor_orders__vendor'
        ),
        id=order_id
    )

    return render(
        request,
        'custom_admin_templates/all_order_detail.html',
        {
            'order': order
        }
    )

# def order_detail(request, order_id):
#     if not request.user.is_authenticated:
#         return redirect('panel_login')
#     if request.user.role == 'customer':
#         return redirect('shop')

#     order = get_object_or_404(Order, id=order_id)
#     items = order.items.all()

#     return render(request, 'custom_admin_templates/order_detail.html', {
#         'order': order,
#         'items': items,
#     })


def update_order_status(request, order_id):

    if not request.user.is_authenticated:
        return redirect('panel_login')

    if request.user.role not in ('admin', 'vendor'):
        return redirect('shop')

    vendor_order = get_object_or_404(
        VendorOrder,
        id=order_id
    )

    if (
        request.user.role == 'vendor'
        and vendor_order.vendor != request.user
    ):
        from django.contrib import messages as flash
        flash.error(
            request,
            "You do not have permission to update this order."
        )
        return redirect('vendor_orders')

    if request.method == 'POST':

        new_status = request.POST.get('status')

        valid_statuses = (
            'pending',
            'processing',
            'shipped',
            'Done',
            'Cancelled'
        )

        if new_status in valid_statuses:

            vendor_order.status = new_status
            vendor_order.save()

            from django.contrib import messages as flash
            flash.success(
                request,
                f'Order #{vendor_order.order.id} status updated.'
            )

    return redirect(
        'order_detail',
        order_id=vendor_order.id
    )
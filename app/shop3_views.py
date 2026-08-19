import http
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
from django.urls import reverse
from app.models import Product, Category
from django.core.paginator import Paginator
# from app.models import Product, Category, Cart ,Wishlist, Profile ,Coupon,CartOrder,Order,OrderItem
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model, login, authenticate
from django import forms
from django.utils import timezone
from .models import Product, Category, Wishlist,CartOrder,Coupon,Order,OrderItem,Cart,Profile,SiteProfile,background_image_aat_index_page,booktable
from django.contrib.sites.shortcuts import get_current_site
from app.models import SiteProfile


from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def custom_admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = "Invalid credentials or you do not have admin access."
            return render(request, 'custom_admin/pages-sign-in.html', {'error_message': error_message})
    return render(request, 'custom_admin/pages-sign-in.html')

@login_required(login_url='custom_admin_login')
def dashboard(request):
    if not request.user.is_superuser:
        return http.HttpResponseForbidden("You are not authorized to access this page.")
    return render(request, "custom_admin/index.html")


def book_table(request):
    current_site=get_current_site(request)
    site_profile=SiteProfile.objects.get(site=current_site)

    if request.method == "POST":
        book_table=booktable.objects.create(

            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            number_of_guests=request.POST.get('number_of_guests')
        )
        return redirect('index')

    return render(request,site_profile.template_name,{'site_profile':site_profile})

def product_view(request):
    products = Product.objects.select_related('category', 'domain').order_by('id')
    categories = Category.objects.all()
    companies=Product.objects.values_list('company', flat=True).distinct()
    sites=Site.objects.all()

    search = request.GET.get('s', '').strip()
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search) |
            Q(company__icontains=search)|
            Q(id__icontains=search)
        )

    category = request.GET.get('category')
    company = request.GET.get('company')
    domain_id = request.GET.get('site')
    is_new = request.GET.get('is_new')

    if category:
        products = products.filter(category__id=category)
        categories = categories.filter(id=category)
        companies = companies.filter(category__id=category)

    if company:
        products = products.filter(company__icontains=company)

    if domain_id:
        products = products.filter(domain__id=domain_id)
        categories = categories.filter(domain__id=domain_id)

    if is_new == 'true':
        products = products.filter(is_new=True)
    elif is_new == 'false':
        products = products.filter(is_new=False)


    sort= request.GET.get('sort', 'id')
    if sort in ['id', '-id', 'name', '-name', "price", "-price"]:
        products = products.order_by(sort)
    else:
        products = products.order_by('id')

    context = {
        "products": products,
        "search": search,
        "categories": categories,
        "sites": sites,
        "companies": companies
    }

    

    return render(request, 'custom_admin/pages-blank.html', context)

def bulk_delete_products(request):
    if request.method == "POST":
        ids = request.POST.getlist('ids')
        Product.objects.filter(id__in=ids).delete()
        messages.success(request, "Selected products deleted successfully.")

    return redirect('product_view')


def product_preview(request, product_id):
    product=get_object_or_404(Product, id=product_id)
    categories=Category.objects.all()
    sites=Site.objects.all()

    if request.method=="POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.company = request.POST.get("company")
        product.description = request.POST.get("description")

        category_id = request.POST.get("category")
        if category_id:
            product.category = Category.objects.get(id=category_id)

        site_id = request.POST.get("site")
        if site_id:
            product.site = SiteProfile.objects.get(id=site_id)

        domain_id = request.POST.get("domain")
        if domain_id:
            product.domain = SiteProfile.objects.get(id=domain_id)

        product.is_new = request.POST.get("is_new") == "on"

        discount_percent = request.POST.get("discount_percent")
        if discount_percent:
            product.discount_percent = discount_percent

        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        discount_start_date = request.POST.get("discount_start_date")
        discount_end_date = request.POST.get("discount_end_date")

        if discount_start_date:
            product.discount_start_date = discount_start_date

        if discount_end_date:
            product.discount_end_date = discount_end_date

        product.save()

        messages.success(request, "Product updated successfully!")

        return redirect("product_preview", product_id=product.id)

    context = {
        "product": product,
        "categories": categories,
        "sites": sites,
    }

    return render(request, "custom_admin/product_preview.html", context)

def product_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_view') 
    return redirect('product_preview', product_id=product.id)


def add_product(request):

    categories=Category.objects.all()
    sites=Site.objects.all()

    if request.method=="POST":

        Product.objects.create(
            domain_id=request.POST.get("domain"),
            site_id=request.POST.get("site"),
            name=request.POST.get("name"),
            category_id=request.POST.get("category"),
            image=request.FILES.get("image"),
            price=request.POST.get("price"),
            company=request.POST.get("company", "Generic"),
            description=request.POST.get("description", "No description available."),
            has_discount=True if request.POST.get("has_discount") == "on" else False,
            discount_percent=request.POST.get("discount_percent") or None,
            discount_start_date=request.POST.get("discount_start_date") or None,
            discount_end_date=request.POST.get("discount_end_date") or None,
            is_new=True if request.POST.get("is_new") == "on" else False
        )

        return redirect('product_view')
    
    return render(request, "custom_admin/add_product.html", {"categories": categories, "sites": sites})
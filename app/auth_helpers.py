"""
Authorization helper functions for object-level access control.
Use these functions to check if a user has permission to access specific objects.
"""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Product, VendorOrder, OrderItem


def check_product_access(user, product):
    """
    Check if user has access to view/edit/delete a product.
    Admins can access all products.
    Vendors can only access their own products.
    
    Args:
        user: CustomUser instance
        product: Product instance
        
    Raises:
        PermissionDenied: If user doesn't have access
    """
    if user.role == 'admin':
        return True
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        if product.vendor_id == user.id:
            return True
        raise PermissionDenied('You do not have permission to access this product.')
    else:
        raise PermissionDenied('You do not have permission to access this resource.')


def get_product_or_403(user, product_id):
    """
    Get a product object or raise PermissionDenied.
    For vendors, only returns their own products.
    For admins, returns any product.
    
    Args:
        user: CustomUser instance
        product_id: Product ID to fetch
        
    Returns:
        Product instance
        
    Raises:
        Http404: If product doesn't exist
        PermissionDenied: If user doesn't have access
    """
    if user.role == 'admin':
        return get_object_or_404(Product, id=product_id)
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        return get_object_or_404(Product, id=product_id, vendor=user)
    else:
        raise PermissionDenied('You do not have permission to access this resource.')


def check_vendor_order_access(user, vendor_order):
    """
    Check if user has access to view a vendor order.
    Admins can access all vendor orders.
    Vendors can only access their own vendor orders.
    
    Args:
        user: CustomUser instance
        vendor_order: VendorOrder instance
        
    Raises:
        PermissionDenied: If user doesn't have access
    """
    if user.role == 'admin':
        return True
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        if vendor_order.vendor_id == user.id:
            return True
        raise PermissionDenied('You do not have permission to access this order.')
    else:
        raise PermissionDenied('You do not have permission to access this resource.')


def get_vendor_order_or_403(user, vendor_order_id):
    """
    Get a vendor order or raise PermissionDenied.
    For vendors, only returns their own vendor orders.
    For admins, returns any vendor order.
    
    Args:
        user: CustomUser instance
        vendor_order_id: VendorOrder ID to fetch
        
    Returns:
        VendorOrder instance
        
    Raises:
        Http404: If order doesn't exist
        PermissionDenied: If user doesn't have access
    """
    if user.role == 'admin':
        return get_object_or_404(VendorOrder, id=vendor_order_id)
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        return get_object_or_404(VendorOrder, id=vendor_order_id, vendor=user)
    else:
        raise PermissionDenied('You do not have permission to access this resource.')


def get_order_items_for_user(user, order):
    """
    Get order items visible to the user.
    Admins see all items.
    Vendors see only their items.
    
    Args:
        user: CustomUser instance
        order: Order instance
        
    Returns:
        QuerySet of OrderItem
        
    Raises:
        PermissionDenied: If user is not admin and has no items in order
    """
    from django.db.models import Q
    
    if user.role == 'admin':
        return order.items.all()
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        items = order.items.filter(product__vendor=user)
        if not items.exists():
            raise PermissionDenied('You do not have permission to access this order.')
        return items
    else:
        raise PermissionDenied('You do not have permission to access this resource.')


def can_edit_product(user, product):
    """
    Check if user can edit a product.
    
    Args:
        user: CustomUser instance
        product: Product instance
        
    Returns:
        bool: True if can edit, raises PermissionDenied otherwise
    """
    check_product_access(user, product)
    return True


def can_delete_product(user, product):
    """
    Check if user can delete a product.
    Currently same as edit permissions, but can be extended.
    
    Args:
        user: CustomUser instance
        product: Product instance
        
    Returns:
        bool: True if can delete, raises PermissionDenied otherwise
    """
    check_product_access(user, product)
    return True


def filter_products_for_user(user, queryset=None):
    """
    Filter a product queryset based on user permissions.
    
    Args:
        user: CustomUser instance
        queryset: Optional Product QuerySet to filter (default: all products)
        
    Returns:
        Filtered QuerySet
    """
    if queryset is None:
        queryset = Product.objects.all()
    
    if user.role == 'admin':
        return queryset
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        return queryset.filter(vendor=user)
    else:
        return queryset.none()


def filter_vendor_orders_for_user(user, queryset=None):
    """
    Filter a vendor order queryset based on user permissions.
    
    Args:
        user: CustomUser instance
        queryset: Optional VendorOrder QuerySet to filter (default: all orders)
        
    Returns:
        Filtered QuerySet
    """
    if queryset is None:
        queryset = VendorOrder.objects.all()
    
    if user.role == 'admin':
        return queryset
    elif user.role == 'vendor' and user.vendor_status == 'approved':
        return queryset.filter(vendor=user)
    else:
        return queryset.none()

"""
Cache utilities for managing cached data with proper invalidation.
Handles cache keys and invalidation strategies for products and vendor data.
"""

from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import decorator_from_middleware_with_args
from django.views.decorators.cache import never_cache


# Cache timeout constants (in seconds)
CACHE_TIMEOUT_PRODUCT = 3600  # 1 hour
CACHE_TIMEOUT_STORE = 3600  # 1 hour
CACHE_TIMEOUT_CATEGORY = 3600  # 1 hour
CACHE_TIMEOUT_ADMIN_DASH = 300  # 5 minutes


# Cache key patterns
def get_product_cache_key(product_id):
    """Generate cache key for a product."""
    return f'product_{product_id}'


def get_products_cache_key(site_id=None):
    """Generate cache key for product list."""
    if site_id:
        return f'products_shop_{site_id}'
    return 'products_shop_all'


def get_product_cache_keys(product_id):
    """Get all cache keys related to a product for invalidation."""
    return [
        get_product_cache_key(product_id),
        'products_shop_all',
        'categories_all',
    ]


def get_vendor_products_cache_key(vendor_id):
    """Generate cache key for vendor's products."""
    return f'vendor_products_{vendor_id}'


def get_vendor_dashboard_cache_key(vendor_id):
    """Generate cache key for vendor dashboard."""
    return f'vendor_dashboard_{vendor_id}'


def get_admin_dashboard_cache_key():
    """Generate cache key for admin dashboard."""
    return 'admin_dashboard'


def get_vendor_orders_cache_key(vendor_id):
    """Generate cache key for vendor orders."""
    return f'vendor_orders_{vendor_id}'


def invalidate_product_cache(product_id):
    """
    Invalidate all cache related to a product.
    Called when product is created/updated/deleted.
    """
    keys = get_product_cache_keys(product_id)
    cache.delete_many(keys)


def invalidate_vendor_cache(vendor_id):
    """
    Invalidate all cache related to a vendor.
    Called when vendor status changes, products change, etc.
    """
    keys = [
        get_vendor_products_cache_key(vendor_id),
        get_vendor_dashboard_cache_key(vendor_id),
        get_vendor_orders_cache_key(vendor_id),
        get_admin_dashboard_cache_key(),
        'products_shop_all',
    ]
    cache.delete_many(keys)


def invalidate_admin_cache():
    """
    Invalidate admin dashboard and related data.
    Called when vendors approved/rejected/suspended.
    """
    keys = [
        get_admin_dashboard_cache_key(),
        'products_shop_all',
        'categories_all',
    ]
    cache.delete_many(keys)


def get_or_set_product(product_id, getter_func):
    """
    Get a product from cache or call getter_func to fetch and cache it.
    
    Args:
        product_id: Product ID
        getter_func: Callable that returns the product
        
    Returns:
        Product instance
    """
    cache_key = get_product_cache_key(product_id)
    product = cache.get(cache_key)
    
    if product is None:
        product = getter_func()
        if product:
            cache.set(cache_key, product, CACHE_TIMEOUT_PRODUCT)
    
    return product


def cache_public_page(timeout=3600):
    """
    Decorator for caching public pages (products, stores, categories).
    Do NOT use for authenticated/personalized pages.
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(view_func):
        # Use Django's cache_page but with proper cache control headers
        return cache_page(timeout)(view_func)
    return decorator


def never_cache_page(view_func):
    """
    Decorator to prevent caching of sensitive pages.
    Use for vendor dashboards, admin panels, user-specific data.
    """
    return never_cache(view_func)

"""
Authorization decorators for role-based access control.
Use these decorators to protect views based on user roles and vendor status.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """
    Decorator to check if user is admin.
    Redirects to login if not authenticated, shows error if not admin.
    """
    @wraps(view_func)
    @login_required(login_url='panel_login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'You do not have permission to access this resource.')
            return redirect('panel_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def vendor_approved_required(view_func):
    """
    Decorator to check if user is an approved vendor.
    - Pending vendors are redirected with a message
    - Rejected vendors are redirected with rejection reason
    - Suspended vendors are redirected with suspension message
    - Non-vendors are redirected to shop
    """
    @wraps(view_func)
    @login_required(login_url='panel_login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'vendor':
            if request.user.role == 'customer':
                messages.error(request, 'Customers cannot access the vendor panel.')
                return redirect('shop')
            messages.error(request, 'You do not have permission to access this resource.')
            return redirect('panel_login')
        
        # Check vendor status
        if request.user.vendor_status == 'pending':
            messages.warning(
                request,
                'Your vendor account is pending admin approval. Please wait for approval.'
            )
            return redirect('panel_login')
        elif request.user.vendor_status == 'rejected':
            reason = request.user.vendor_rejection_reason or 'No reason provided.'
            messages.error(
                request,
                f'Your vendor request has been rejected. Reason: {reason}'
            )
            return redirect('panel_login')
        elif request.user.vendor_status == 'suspended':
            messages.error(
                request,
                'Your vendor account is currently suspended. Please contact the administrator.'
            )
            return redirect('panel_login')
        elif request.user.vendor_status != 'approved':
            messages.error(request, 'Your vendor account status is invalid.')
            return redirect('panel_login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def vendor_or_admin_required(view_func):
    """
    Decorator for views that can be accessed by approved vendors or admins.
    """
    @wraps(view_func)
    @login_required(login_url='panel_login')
    def wrapper(request, *args, **kwargs):
        if request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        elif request.user.role == 'vendor' and request.user.vendor_status == 'approved':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'You do not have permission to access this resource.')
            return redirect('panel_login')
    return wrapper


def customer_required(view_func):
    """
    Decorator to check if user is a customer.
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'customer':
            messages.error(request, 'This page is only for customers.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

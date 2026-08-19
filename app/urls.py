from django.urls import path
from app import views, shop3_views
from django.conf import settings  
from django.conf.urls.static import static 
from django.contrib.auth import views as auth_views
from app import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api_views import LoginView  


urlpatterns = [
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('product/', views.product, name='product'),
    path('checkout/', views.checkout, name='checkout'),
    path('blank/', views.blank, name='blank'),
    path('categories/', views.categories, name='categories'),
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('shop/quick_view/', views.quick_view, name='quick_view'),
    path('cart/',views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('account/', views.account, name='account'),
    path('book_table/', shop3_views.book_table, name='book_table'),
    path('custom_admin/', shop3_views.dashboard, name='dashboard'),
    path('custom_admin/login/', shop3_views.custom_admin_login, name='custom_admin_login'),
    path('custom_admin/product_view/', shop3_views.product_view, name='product_view'),
    path('bulk-delete-products/', shop3_views.bulk_delete_products, name='bulk_delete_products'),
    path('product-preview/<int:product_id>/', shop3_views.product_preview, name='product_preview'),
    path('product-delete/<int:product_id>/', shop3_views.product_delete_view, name='product_delete'),
    path('add-product/', shop3_views.add_product, name='add_product'),
    path('send-whatsapp/', views.send_whatsapp_message, name='send_whatsapp'),
    # path('send-whatsapp/', views.send_buttons, name='send_whatsapp'),
    # path('webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),




    path('api/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('api/account/', api_views.AccountView.as_view(), name='api_account'),
    path('api/products/', api_views.ProductListView.as_view(), name='api_products'),
    path('api/products/<int:pk>/', api_views.ProductDetailView.as_view(), name='api_product_detail'),
    path('api/categories/', api_views.CategoryListView.as_view(), name='api_categories'),
    path('api/cart/', api_views.CartView.as_view(), name='api_cart'),
    path('api/cart/add/<int:product_id>/', api_views.AddToCartView.as_view(), name='api_add_to_cart'),
    path('api/cart/remove/<int:item_id>/', api_views.RemoveFromCartView.as_view(), name='api_remove_from_cart'),
    path('api/cart/update/<int:item_id>/', api_views.UpdateCartView.as_view(), name='api_update_cart'),
    path('api/wishlist/', api_views.WishlistView.as_view(), name='api_wishlist'),
    path('api/wishlist/toggle/<int:product_id>/', api_views.ToggleWishlistView.as_view(), name='api_toggle_wishlist'),
    path('api/checkout/', api_views.CheckoutView.as_view(), name='api_checkout'),
    path('api/orders/', api_views.OrderListView.as_view(), name='api_orders'),
    path('api/login/', LoginView.as_view(), name='api-login'),




    path('panel/login/',                                           views.panel_login,          name='panel_login'),
    path('panel/logout/',                                          views.panel_logout,         name='panel_logout'),

    path('panel/vendor/',                                          views.vendor_dashboard,     name='vendor_dashboard'),
    path('panel/vendor/customers/',                                views.vendor_customers,     name='vendor_customers'),
    path('panel/vendor/orders/',                                   views.vendor_orders,        name='vendor_orders'),
    path('panel/order/<int:order_id>/',                            views.order_detail,         name='order_detail'),
    path('panel/all-order/<int:order_id>/',                        views.all_order_detail       ,name='all_order_detail'),
    path('panel/vendor/products/',                                 views.my_products,          name='my_products'),
    path('panel/vendor/products/add/',                             views.product_add,          name='panel_product_add'),
    path('panel/vendor/products/detail/<int:product_id>/',         views.panel_product_detail, name='panel_product_detail'),
    path('panel/vendor/products/delete/<int:product_id>/',         views.product_delete,       name='panel_product_delete'),
    path('panel/vendor/categories/',                             views.manage_categories, name='manage_categories'),
    path('panel/vendor/categories/add/',                         views.category_add,      name='category_add'),
    path('panel/vendor/categories/edit/<int:category_id>/',      views.category_edit,     name='category_edit'),
    path('panel/vendor/categories/delete/<int:category_id>/',    views.category_delete,   name='category_delete'),
    path('panel/vendor/carts/',                            views.view_carts, name='view_carts'),
    path('panel/vendor/coupons/',                          views.manage_coupons, name='manage_coupons'),
    path('panel/vendor/coupons/add/',                      views.coupon_add,     name='coupon_add'),
    path('panel/vendor/coupons/edit/<int:coupon_id>/',     views.coupon_edit,    name='coupon_edit'),
    path('panel/vendor/coupons/delete/<int:coupon_id>/',   views.coupon_delete,  name='coupon_delete'),
    path('panel/vendor/coupons/toggle/<int:coupon_id>/',   views.coupon_toggle,  name='coupon_toggle'),
    # path('panel/vendor/orders/',                          views.vendor_orders,       name='vendor_orders'),
    path('panel/admin/orders/',                           views.all_orders,          name='all_orders'),
    path('panel/admin/orders/status/<int:order_id>/',     views.update_order_status, name='update_order_status'),

    path('panel/admin/',                                           views.admin_dashboard,      name='admin_dashboard'),
    path('panel/admin/vendors/',                                   views.manage_vendors,       name='manage_vendors'),
    path('panel/admin/vendors/approve/<int:user_id>/',             views.approve_vendor,       name='approve_vendor'),
    path('panel/admin/vendors/reject/<int:user_id>/',              views.reject_vendor,        name='reject_vendor'),
    path('panel/admin/vendors/suspend/<int:user_id>/',             views.suspend_vendor,       name='suspend_vendor'),
    path('panel/admin/vendors/reactivate/<int:user_id>/',          views.reactivate_vendor,    name='reactivate_vendor'),
    path('panel/admin/users/',                                     views.manage_users,         name='manage_users'),
    path('panel/admin/users/ban/<int:user_id>/',                   views.ban_user,             name='ban_user'),
    path('panel/admin/users/unban/<int:user_id>/',                 views.unban_user,           name='unban_user'),
    path('panel/admin/users/role/<int:user_id>/',                  views.change_user_role,     name='change_user_role'),
    
   
]
     






if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Product, Wishlist, Cart


@receiver(user_logged_in)
def merge_cart(sender, request, user, **kwargs):
    session_cart = request.session.get('cart', {})

    for product_id, quantity in session_cart.items():
        product = Product.objects.get(id=product_id)

        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product
        )

        cart_item.quantity += quantity
        cart_item.save()

    request.session.pop('cart', None)

@receiver(user_logged_in)
def merge_wishlist(sender, request, user, **kwargs):
    session_wishlist = request.session.get('wishlist', [])

    for product_id in session_wishlist:
        product = Product.objects.filter(id=product_id).first()
        if product:
            Wishlist.objects.get_or_create(
                user=user,
                product=product
            )

    request.session.pop('wishlist', None)
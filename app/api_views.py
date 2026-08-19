from requests import request
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from .models import (
    Product, Category, Cart, CartOrder,
    Wishlist, Order, OrderItem, Coupon,
    Profile, SiteProfile
)
from .serializers import (
    ProductSerializer, CategorySerializer, CartSerializer,
    CartOrderSerializer, WishlistSerializer, OrderSerializer,
    RegisterSerializer, ProfileSerializer
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        User = get_user_model()
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'username': str(user),
                    'message': 'Login successful'
                })
        except User.DoesNotExist:
            pass

        return Response(
            {'error': 'Email or password is incorrect.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Product.objects.all()
        category = self.request.GET.get('category')
        company = self.request.GET.get('company')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        q = self.request.GET.get('q')

        if category:
            qs = qs.filter(category__name=category)
        if company:
            qs = qs.filter(company=company)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(company__icontains=q)
            )
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]



class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]



class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Cart.objects.filter(user=request.user)
        cart_order, _ = CartOrder.objects.get_or_create(user=request.user)
        return Response({
            'items': CartSerializer(items, many=True).data,
            'cart_total': cart_order.cart_total(),
            'discount': cart_order.discount_amount(),
            'final_total': cart_order.final_total(),
        })

    def post(self, request):
        code = request.data.get('coupon_code', '').strip()
        if code:
            try:
                coupon = Coupon.objects.get(code__iexact=code)
                cart_order, _ = CartOrder.objects.get_or_create(user=request.user)
                if coupon.is_valid():
                    cart_order.coupon = coupon
                    cart_order.save()
                    return Response({'message': 'Coupon applied successfully'})
                return Response({'message': 'Coupon expired or inactive'}, status=400)
            except Coupon.DoesNotExist:
                return Response({'message': 'Invalid coupon code'}, status=400)
        return Response({'message': 'No coupon code provided'}, status=400)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        return Response({'message': 'Added to cart', 'quantity': cart_item.quantity})


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        item = get_object_or_404(Cart, id=item_id, user=request.user)
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
        return Response({'message': 'Cart updated'})


class UpdateCartView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        item = get_object_or_404(Cart, id=item_id, user=request.user)
        quantity = int(request.data.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
        return Response({'message': 'Cart updated'})



class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Wishlist.objects.filter(user=request.user)
        return Response(WishlistSerializer(items, many=True).data)


class ToggleWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist'})
        return Response({'message': 'Added to wishlist'})



class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=400)

        cart_order, _ = CartOrder.objects.get_or_create(user=request.user)
        data = request.data

        order = Order.objects.create(
            user=request.user,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            total_amount=cart_order.final_total()
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.discounted_price()
            )

        cart_items.delete()

        items_list = "\n".join([f"{i.product.name} x {i.quantity}" for i in order.items.all()])
        send_mail(
            "Order Confirmation",
            f"Dear {order.first_name},\n\nYour order:\n{items_list}\n\nTotal: Rs {order.total_amount}\n\nThank you!",
            settings.EMAIL_HOST_USER,
            [order.email],
            fail_silently=True
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)



class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class AccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = ProfileSerializer(user.profile).data
        except Profile.DoesNotExist:
            profile = None
        return Response({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': profile,
            # 'password':user.password,
            
        })
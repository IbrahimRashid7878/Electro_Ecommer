from rest_framework import serializers
from .models import (
    Product, Category, Cart, CartOrder,
    Wishlist, Order, OrderItem, Coupon, Profile
)
from django.contrib.auth import get_user_model

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    discounted_price = serializers.SerializerMethodField()
    discount_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_id', 'stock_qty',
            'image', 'price', 'discounted_price', 'company',
            'description', 'has_discount', 'discount_percent',
            'discount_start_date', 'discount_end_date',
            'discount_active', 'is_new'
        ]

    def get_discounted_price(self, obj):
        return obj.discounted_price()


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']


class CartOrderSerializer(serializers.ModelSerializer):
    cart_total = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    final_total = serializers.SerializerMethodField()

    class Meta:
        model = CartOrder
        fields = ['id', 'coupon', 'cart_total', 'discount_amount', 'final_total']

    def get_cart_total(self, obj): return obj.cart_total()
    def get_discount_amount(self, obj): return obj.discount_amount()
    def get_final_total(self, obj): return obj.final_total()


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'address', 'city', 'country', 'zip_code', 'phone',
            'total_amount', 'created_at', 'status', 'items'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['age', 'picture']
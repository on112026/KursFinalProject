from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from typing import List, Dict, Any
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct, Sale, ProductSale

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_company_owner']
        extra_kwargs = {
            'username': {'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        # По умолчанию is_staff = True для доступа в админку
        user.is_staff = True
        user.save()
        return user

class CompanySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'inn', 'name', 'owner']

class StorageSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Storage
        fields = ['id', 'address', 'company']

class SupplierSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'inn', 'contact_info', 'company']
        read_only_fields = ['company']

class SupplierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'inn', 'contact_info']

class ProductSerializer(serializers.ModelSerializer):
    storage = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'sale_price', 'quantity', 'storage']
        read_only_fields = ['storage']

class ProductCreateSerializer(serializers.ModelSerializer):
    storage_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'sale_price', 'storage_id']

class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка товаров (без storage_id)"""
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'sale_price', 'quantity']

class SupplySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier', 'supplier_name', 'storage', 'delivery_date']

class SupplyProductSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = SupplyProduct
        fields = ['id', 'product', 'product_title', 'quantity']

class SupplyCreateSerializer(serializers.Serializer):
    """Сериализатор для создания поставки"""
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value

class AttachUserSerializer(serializers.Serializer):
    """Сериализатор для прикрепления пользователя к компании"""
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, data):
        if not data.get('user_id') and not data.get('email'):
            raise serializers.ValidationError("Either 'user_id' or 'email' must be provided")
        return data


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для сотрудников компании"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_company_owner']


class SupplyCreateResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при создании поставки"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    products = serializers.SerializerMethodField()
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier_name', 'delivery_date', 'products']
    
    def get_products(self, obj) -> List[Dict[str, Any]]:
        return list(SupplyProduct.objects.filter(supply=obj).values(
            'product__id', 'product__title', 'quantity'
        ))

class SupplyListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка поставок"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier_name', 'delivery_date']


# ===== Sale Serializers =====

class ProductSaleSerializer(serializers.ModelSerializer):
    """Сериализатор для ProductSale (связь продажи и товара)"""
    product_title = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = ProductSale
        fields = ['id', 'product', 'product_title', 'quantity', 'price']
        read_only_fields = ['id', 'product_title', 'price']


class ProductSaleCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ProductSale в составе Sale"""
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class SaleSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра продажи"""
    product_sales = ProductSaleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'buyer_name', 'sale_date', 'total_amount', 'product_sales']
        read_only_fields = ['id', 'total_amount']


class SaleCreateSerializer(serializers.Serializer):
    """Сериализатор для создания продажи"""
    buyer_name = serializers.CharField(max_length=255)
    product_sales = ProductSaleCreateSerializer(many=True)


class SaleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка продаж"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = ['id', 'buyer_name', 'sale_date', 'total_amount', 'product_count']
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_product_count(self, obj) -> int:
        return obj.product_sales.count()


class SaleUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления продажи - только buyer_name и sale_date"""
    
    class Meta:
        model = Sale
        fields = ['buyer_name', 'sale_date']
    
    def validate_sale_date(self, value):
        """Дата продажи может быть только в прошлое или сегодня"""
        from django.utils import timezone
        from datetime import datetime, time
        
        today = timezone.now().date()
        if value.date() > today:
            raise serializers.ValidationError("Дата продажи не может быть в будущем")
        return value
    
    def update(self, instance, validated_data):
        # Обновляем buyer_name если передан
        if 'buyer_name' in validated_data:
            instance.buyer_name = validated_data['buyer_name']
        
        # Обновляем sale_date если передан
        if 'sale_date' in validated_data:
            instance.sale_date = validated_data['sale_date']
        
        instance.save()
        return instance

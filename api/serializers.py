from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from typing import List, Dict, Any
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct

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
        fields = ['id', 'name', 'contact_info', 'company']
        read_only_fields = ['company']

class SupplierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_info']

class ProductSerializer(serializers.ModelSerializer):
    storage = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'quantity', 'storage']
        read_only_fields = ['storage']

class ProductCreateSerializer(serializers.ModelSerializer):
    storage_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'storage_id']

class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка товаров (без storage_id)"""
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'purchase_price', 'quantity']

class SupplySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier', 'supplier_name', 'storage', 'date']

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


class SupplyCreateResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при создании поставки"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    products = serializers.SerializerMethodField()
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier_name', 'date', 'products']
    
    def get_products(self, obj) -> List[Dict[str, Any]]:
        return list(SupplyProduct.objects.filter(supply=obj).values(
            'product__id', 'product__title', 'quantity'
        ))

class SupplyListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка поставок"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Supply
        fields = ['id', 'supplier_name', 'date']

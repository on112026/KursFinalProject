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
        fields = ['id', 'buyer_name', 'date', 'total_amount', 'product_sales']
        read_only_fields = ['id', 'date', 'total_amount']


class SaleCreateSerializer(serializers.Serializer):
    """Сериализатор для создания продажи"""
    buyer_name = serializers.CharField(max_length=255)
    product_sales = ProductSaleCreateSerializer(many=True)


class SaleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка продаж"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = ['id', 'buyer_name', 'date', 'total_amount', 'product_count']
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_product_count(self, obj) -> int:
        return obj.product_sales.count()


class SaleUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления продажи"""
    product_sales = ProductSaleCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Sale
        fields = ['buyer_name', 'product_sales']
    
    def update(self, instance, validated_data):
        product_sales_data = validated_data.pop('product_sales', None)
        
        # Обновляем buyer_name если передан
        if 'buyer_name' in validated_data:
            instance.buyer_name = validated_data['buyer_name']
            instance.save()
        
        # Если переданы product_sales, обновляем их
        if product_sales_data is not None:
            # Удаляем старые связи
            instance.product_sales.all().delete()
            
            total_amount = 0
            for item in product_sales_data:
                product_id = item['product']
                quantity = item['quantity']
                
                try:
                    product = Product.objects.get(id=product_id, storage=instance.company.storage)
                except Product.DoesNotExist:
                    raise serializers.ValidationError(f"Product with id {product_id} not found")
                
                # Используем purchase_price как цену продажи
                price = product.purchase_price
                
                ProductSale.objects.create(
                    sale=instance,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                total_amount += price * quantity
            
            instance.total_amount = total_amount
            instance.save()
        
        return instance

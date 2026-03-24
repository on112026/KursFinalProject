from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_field, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct, Sale, ProductSale
from .serializers import (
    UserSerializer, CompanySerializer, StorageSerializer,
    SupplierSerializer, SupplierCreateSerializer,
    ProductSerializer, ProductCreateSerializer, ProductListSerializer,
    SupplySerializer, SupplyCreateSerializer, SupplyListSerializer, SupplyCreateResponseSerializer,
    AttachUserSerializer,
    SaleSerializer, SaleCreateSerializer, SaleListSerializer, SaleUpdateSerializer,
    ProductSaleSerializer
)
from django.utils import timezone
from datetime import datetime
from rest_framework.exceptions import PermissionDenied
from django.db import transaction


def get_user_company(user):
    """Получить компанию пользователя (владелец или привязанный пользователь)"""
    # Проверяем, является ли пользователь владельцем компании
    if hasattr(user, 'company') and user.company:
        return user.company
    
    # Проверяем, привязан ли пользователь к какой-либо компании
    from .models import Company
    company = Company.objects.filter(users=user).first()
    return company


class RegisterView(GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_staff = True
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class CreateCompanyView(GenericAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'company') and request.user.company:
            return Response({'error': 'User already has a company'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save(owner=request.user)
            # Устанавливаем is_company_owner = True для владельца
            request.user.is_company_owner = True
            request.user.save()
            return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetCompanyView(GenericAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        return Response(CompanySerializer(request.user.company).data)


class UpdateCompanyView(GenericAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.company.owner != request.user:
            raise PermissionDenied('Only company owner can update company')

        serializer = CompanySerializer(request.user.company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(CompanySerializer(request.user.company).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCompanyView(GenericAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.company.owner != request.user:
            raise PermissionDenied('Only company owner can delete company')

        request.user.company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetStorageView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="storage_list")
    def get(self, request):
        if not hasattr(request.user, 'company') or not request.user.company or not hasattr(request.user.company, 'storage') or not request.user.company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(StorageSerializer(request.user.company.storage).data)


class GetStorageByIdView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="storage_retrieve")
    def get(self, request, storage_id):
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        if storage.company.owner != request.user and not storage.company.users.filter(id=request.user.id).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        return Response(StorageSerializer(storage).data)


class CreateStorageView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({'error': 'User must have a company to create storage'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(request.user.company, 'storage') and request.user.company.storage:
            return Response({'error': 'Company already has a storage'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StorageSerializer(data=request.data)
        if serializer.is_valid():
            storage = serializer.save(company=request.user.company)
            return Response(StorageSerializer(storage).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateStorageView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, storage_id):
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        if storage.company.owner != request.user:
            raise PermissionDenied('Only company owner can update storage')

        serializer = StorageSerializer(storage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(StorageSerializer(storage).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteStorageView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, storage_id):
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        if storage.company.owner != request.user:
            raise PermissionDenied('Only company owner can update storage')

        storage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===== Supplier Views =====

class SupplierListCreateView(GenericAPIView):
    """Список поставщиков компании / Создание поставщика"""
    serializer_class = SupplierCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="suppliers_list")
    def get(self, request):
        """Получить список поставщиков компании"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        suppliers = Supplier.objects.filter(company=company)
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        """Создать нового поставщика"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupplierCreateSerializer(data=request.data)
        if serializer.is_valid():
            supplier = serializer.save(company=company)
            return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierDetailView(GenericAPIView):
    """Получить / Изменить / Удалить поставщика"""
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, supplier_id, user):
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return None
        
        # Проверка доступа: владелец компании, пользователь компании или админ
        if supplier.company.owner != user and not supplier.company.users.filter(id=user.id).exists() and not user.is_staff:
            return None
        return supplier

    @extend_schema(operation_id="suppliers_retrieve")
    def get(self, request, supplier_id):
        supplier = self.get_object(supplier_id, request.user)
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SupplierSerializer(supplier).data)

    def put(self, request, supplier_id):
        supplier = self.get_object(supplier_id, request.user)
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupplierCreateSerializer(supplier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(SupplierSerializer(supplier).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, supplier_id):
        supplier = self.get_object(supplier_id, request.user)
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)

        supplier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===== Product Views =====

class ProductListCreateView(GenericAPIView):
    """Список товаров / Создание товара"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ProductListSerializer(many=True)},
        operation_id="products_list"
    )
    def get(self, request):
        """Получить список товаров компании"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(company, 'storage') or not company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(storage=company.storage)
        return Response(ProductListSerializer(products, many=True).data)

    @extend_schema(
        request=ProductCreateSerializer,
        responses={201: ProductSerializer},
        operation_id="products_create"
    )
    def post(self, request):
        """Создать новый товар (quantity = 0)"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(company, 'storage') or not company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(storage=company.storage)
            # Убеждаемся, что quantity = 0
            product.quantity = 0
            product.save()
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(GenericAPIView):
    """Получить / Изменить / Удалить товар"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, product_id, user):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None
        
        # Проверка доступа: пользователь должен быть привязан к компании товара
        if product.storage.company.owner != user and not product.storage.company.users.filter(id=user.id).exists() and not user.is_staff:
            return None
        return product

    @extend_schema(operation_id="products_retrieve")
    def get(self, request, product_id):
        product = self.get_object(product_id, request.user)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    @extend_schema(
        request=ProductCreateSerializer,
        responses={200: ProductSerializer},
        operation_id="products_update"
    )
    def put(self, request, product_id):
        product = self.get_object(product_id, request.user)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Нельзя изменять quantity напрямую - только через поставку
        data = request.data.copy()
        if 'quantity' in data:
            del data['quantity']

        serializer = ProductCreateSerializer(product, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ProductSerializer(product).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id="products_delete")
    def delete(self, request, product_id):
        product = self.get_object(product_id, request.user)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===== Supply Views =====

class SupplyListView(GenericAPIView):
    """Список поставок компании"""
    serializer_class = SupplyListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        supplies = Supply.objects.filter(storage=company.storage)
        return Response(SupplyListSerializer(supplies, many=True).data)


class SupplyCreateView(GenericAPIView):
    """Создание поставки товаров"""
    serializer_class = SupplyCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SupplyCreateSerializer,
        responses={201: SupplyCreateResponseSerializer},
        operation_id="supplies_create"
    )
    def post(self, request):
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(company, 'storage') or not company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        items = request.data
        if not isinstance(items, list) or len(items) == 0:
            return Response({'error': 'Request body must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на отрицательное количество
        for item in items:
            quantity = item.get('quantity')
            if quantity is None or not isinstance(quantity, int) or quantity <= 0:
                return Response({'error': 'All quantities must be positive integers'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем supplier_id из запроса
        supplier_id = request.data[0].get('supplier_id') if len(request.data) > 0 else None
        if not supplier_id:
            return Response({'error': 'supplier_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, что поставщик принадлежит компании
        try:
            supplier = Supplier.objects.get(id=supplier_id, company=company)
        except Supplier.DoesNotExist:
            return Response({'error': 'Supplier not found or does not belong to your company'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                # Создаем поставку
                supply = Supply.objects.create(
                    supplier=supplier,
                    storage=company.storage
                )

                # Обрабатываем товары в поставке
                for item in items:
                    product_id = item.get('id')
                    quantity = item.get('quantity')

                    try:
                        product = Product.objects.get(id=product_id, storage=company.storage)
                    except Product.DoesNotExist:
                        raise ValueError(f"Product with id {product_id} not found")

                    # Увеличиваем количество товара
                    product.quantity += quantity
                    product.save()

                    # Создаем запись в промежуточной таблице
                    SupplyProduct.objects.create(
                        supply=supply,
                        product=product,
                        quantity=quantity
                    )

            return Response(SupplyCreateResponseSerializer(supply).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ===== Company User Attachment Views =====

class AttachUserToCompanyView(GenericAPIView):
    """Прикрепление пользователя к компании (только для владельца)"""
    serializer_class = AttachUserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(description='User attached successfully')},
        operation_id="attach_user_to_company"
    )
    def post(self, request):
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        # Проверка, что пользователь - владелец компании
        if request.user.company.owner != request.user:
            return Response({'error': 'Only company owner can attach users'}, status=status.HTTP_403_FORBIDDEN)

        # Получаем user_id или email из запроса
        user_id = request.data.get('user_id')
        email = request.data.get('email')

        if not user_id and not email:
            return Response({'error': 'user_id or email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user_id:
                user_to_attach = User.objects.get(id=user_id)
            else:
                user_to_attach = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, что пользователь не является владельцем этой компании
        if user_to_attach == request.user:
            return Response({'error': 'Cannot attach yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь не привязан уже к компании
        if request.user.company.users.filter(id=user_to_attach.id).exists():
            return Response({'error': 'User is already attached to this company'}, status=status.HTTP_400_BAD_REQUEST)

        # Привязываем пользователя к компании
        request.user.company.users.add(user_to_attach)

        return Response({
            'message': f'User {user_to_attach.email} has been attached to company {request.user.company.name}'
        }, status=status.HTTP_200_OK)


# ===== Sale Views =====

class SaleCreateView(GenericAPIView):
    """Создание продажи"""
    serializer_class = SaleCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SaleCreateSerializer,
        responses={201: SaleSerializer},
        operation_id="sales_create"
    )
    def post(self, request):
        """Создать новую продажу"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(company, 'storage') or not company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SaleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        buyer_name = serializer.validated_data['buyer_name']
        product_sales_data = serializer.validated_data['product_sales']

        if not product_sales_data or len(product_sales_data) == 0:
            return Response({'error': 'At least one product is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Создаем продажу
                sale = Sale.objects.create(
                    company=company,
                    buyer_name=buyer_name,
                    total_amount=0
                )

                total_amount = 0
                created_product_sales = []

                for item in product_sales_data:
                    product_id = item['product']
                    quantity = item['quantity']

                    try:
                        product = Product.objects.get(id=product_id, storage=company.storage)
                    except Product.DoesNotExist:
                        raise ValueError(f"Product with id {product_id} not found")

                    # Проверяем, что достаточно товара на складе
                    if product.quantity < quantity:
                        raise ValueError(f"Not enough quantity for product '{product.title}'. Available: {product.quantity}")

                    # Используем purchase_price как цену продажи
                    price = product.purchase_price

                    # Уменьшаем количество товара на складе
                    product.quantity -= quantity
                    product.save()

                    # Создаем связь продажи и товара
                    product_sale = ProductSale.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price
                    )
                    created_product_sales.append(product_sale)

                    total_amount += price * quantity

                # Обновляем total_amount
                sale.total_amount = total_amount
                sale.save()

            return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Откатываем изменения, удаляя созданную продажу
            if 'sale' in locals():
                sale.delete()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SaleListView(GenericAPIView):
    """Список продаж компании с фильтрацией по периоду и пагинацией"""
    serializer_class = SaleListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='date_from', type=OpenApiTypes.DATE, description='Filter sales from this date (YYYY-MM-DD)', required=False),
            OpenApiParameter(name='date_to', type=OpenApiTypes.DATE, description='Filter sales until this date (YYYY-MM-DD)', required=False),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, description='Page number', required=False, default=1),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, description='Items per page', required=False, default=10)
        ],
        operation_id="sales_list"
    )
    def get(self, request):
        """Получить список продаж компании с фильтрацией"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        sales = Sale.objects.filter(company=company)

        # Фильтрация по дате
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d')
                sales = sales.filter(date__gte=date_from_parsed)
            except ValueError:
                return Response({'error': 'Invalid date_from format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        if date_to:
            try:
                date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d')
                # Добавляем 1 день, чтобы включить весь день
                from datetime import timedelta
                date_to_parsed = date_to_parsed + timedelta(days=1)
                sales = sales.filter(date__lt=date_to_parsed)
            except ValueError:
                return Response({'error': 'Invalid date_to format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        # Пагинация
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        total_count = sales.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        sales = sales[start:end]

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': SaleListSerializer(sales, many=True).data
        })


class SaleDetailView(GenericAPIView):
    """Получить / Изменить / Удалить продажу"""
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, sale_id, user):
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return None

        # Проверка доступа
        if sale.company.owner != user and not sale.company.users.filter(id=user.id).exists() and not user.is_staff:
            return None
        return sale

    @extend_schema(operation_id="sales_retrieve")
    def get(self, request, sale_id):
        sale = self.get_object(sale_id, request.user)
        if not sale:
            return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SaleSerializer(sale).data)

    @extend_schema(
        request=SaleUpdateSerializer,
        responses={200: SaleSerializer},
        operation_id="sales_update"
    )
    def put(self, request, sale_id):
        sale = self.get_object(sale_id, request.user)
        if not sale:
            return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)

        # Собираем old quantities для возврата на склад
        old_product_sales = {
            ps.product_id: ps.quantity 
            for ps in sale.product_sales.all()
        }

        serializer = SaleUpdateSerializer(sale, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Возвращаем старые товары на склад
                for product_id, quantity in old_product_sales.items():
                    try:
                        product = Product.objects.get(id=product_id)
                        product.quantity += quantity
                        product.save()
                    except Product.DoesNotExist:
                        pass  # Игнорируем, если товар был удален

                # Обновляем продажу
                updated_sale = serializer.save()

                # Возвращаем old quantities для пересчета
                for product_id, quantity in old_product_sales.items():
                    try:
                        product = Product.objects.get(id=product_id)
                        product.quantity -= quantity
                        product.save()
                    except Product.DoesNotExist:
                        pass

                # Уменьшаем количество новых товаров на складе
                new_total = 0
                for ps in updated_sale.product_sales.all():
                    try:
                        product = Product.objects.get(id=ps.product_id)
                        if product.quantity < ps.quantity:
                            raise ValueError(f"Not enough quantity for product '{product.title}'")
                        product.quantity -= ps.quantity
                        product.save()
                    except Product.DoesNotExist:
                        raise ValueError(f"Product not found")

                    new_total += ps.price * ps.quantity

                updated_sale.total_amount = new_total
                updated_sale.save()

            return Response(SaleSerializer(updated_sale).data)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id="sales_delete")
    def delete(self, request, sale_id):
        sale = self.get_object(sale_id, request.user)
        if not sale:
            return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                # Возвращаем товары на склад
                for ps in sale.product_sales.all():
                    product = ps.product
                    product.quantity += ps.quantity
                    product.save()

                sale.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

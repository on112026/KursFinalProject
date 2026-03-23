from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct
from .serializers import (
    UserSerializer, CompanySerializer, StorageSerializer,
    SupplierSerializer, SupplierCreateSerializer,
    ProductSerializer, ProductCreateSerializer, ProductListSerializer,
    SupplySerializer, SupplyCreateSerializer, SupplyListSerializer, SupplyCreateResponseSerializer
)
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

    def get(self, request):
        if not hasattr(request.user, 'company') or not request.user.company or not hasattr(request.user.company, 'storage') or not request.user.company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(StorageSerializer(request.user.company.storage).data)

class GetStorageByIdView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

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
            raise PermissionDenied('Only company owner can delete storage')

        storage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ===== Supplier Views =====

class SupplierListCreateView(GenericAPIView):
    """Список поставщиков компании / Создание поставщика"""
    serializer_class = SupplierCreateSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить список товаров компании"""
        company = get_user_company(request.user)
        if not company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(company, 'storage') or not company.storage:
            return Response({'error': 'Storage not found'}, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(storage=company.storage)
        return Response(ProductListSerializer(products, many=True).data)

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

    def get(self, request, product_id):
        product = self.get_object(product_id, request.user)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

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
    permission_classes = [IsAuthenticated]

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
            supplier = Supplier.objects.get(id=supplier_id, company=request.user.company)
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
    permission_classes = [IsAuthenticated]

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

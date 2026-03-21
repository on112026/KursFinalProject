from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Company, Storage
from .serializers import UserSerializer, CompanySerializer, StorageSerializer
from rest_framework.exceptions import PermissionDenied

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
        try:
            user = User.objects.get(email=request.data['email'])
            if not user.check_password(request.data['password']):
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
        if request.user.company:
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
        if not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        return Response(CompanySerializer(request.user.company).data)

class UpdateCompanyView(GenericAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if not request.user.company:
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
        if not request.user.company:
            return Response({'error': 'User has no company'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.company.owner != request.user:
            raise PermissionDenied('Only company owner can delete company')

        request.user.company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class GetStorageView(GenericAPIView):
    serializer_class = StorageSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.company or not request.user.company.storage:
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
        if not request.user.company:
            return Response({'error': 'User must have a company to create storage'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.company.storage:
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
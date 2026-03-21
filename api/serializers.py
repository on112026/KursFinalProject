from rest_framework import serializers
from .models import User, Company, Storage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_company_owner']
        extra_kwargs = {
            'username': {'required': False}
        }

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'inn', 'name', 'owner']

class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ['id', 'address', 'company']
"""API URL Configuration"""

from django.urls import path
from drf_spectacular.views import SpectacularJSONAPIView
from .views import (
    RegisterView, LoginView, CreateCompanyView, GetCompanyView,
    UpdateCompanyView, DeleteCompanyView, GetStorageView,
    GetStorageByIdView, CreateStorageView, UpdateStorageView,
    DeleteStorageView
)
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('company/create/', CreateCompanyView.as_view(), name='create_company'),
    path('company/', GetCompanyView.as_view(), name='get_company'),
    path('company/update/', UpdateCompanyView.as_view(), name='update_company'),
    path('company/delete/', DeleteCompanyView.as_view(), name='delete_company'),
    path('storage/create/', CreateStorageView.as_view(), name='create_storage'),
    path('storage/', GetStorageView.as_view(), name='get_storage'),
    path('storage/<int:storage_id>/', GetStorageByIdView.as_view(), name='get_storage_by_id'),
    path('storage/update/<int:storage_id>/', UpdateStorageView.as_view(), name='update_storage'),
    path('storage/delete/<int:storage_id>/', DeleteStorageView.as_view(), name='delete_storage'),
    path('schema/', SpectacularJSONAPIView.as_view(), name='openapi-schema'),
    path('swagger/', SpectacularJSONAPIView.as_view(), name='swagger-ui'),
]

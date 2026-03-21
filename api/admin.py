from django.contrib import admin
from .models import User, Company, Storage

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_company_owner']
    search_fields = ['email', 'first_name', 'last_name']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'inn', 'owner']
    search_fields = ['name', 'inn']

@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ['address', 'company']
    search_fields = ['address']
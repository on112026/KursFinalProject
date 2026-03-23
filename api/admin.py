from django.contrib import admin
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_company_owner']
    search_fields = ['email', 'first_name', 'last_name']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'inn', 'owner']
    search_fields = ['name', 'inn']
    filter_horizontal = ['users']

@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ['address', 'company']
    search_fields = ['address']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_info', 'company']
    search_fields = ['name', 'contact_info']
    list_filter = ['company']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'purchase_price', 'quantity', 'storage']
    search_fields = ['title', 'description']
    list_filter = ['storage']

@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'storage', 'date']
    list_filter = ['supplier', 'storage', 'date']
    search_fields = ['supplier__name']

@admin.register(SupplyProduct)
class SupplyProductAdmin(admin.ModelAdmin):
    list_display = ['supply', 'product', 'quantity']
    list_filter = ['supply']

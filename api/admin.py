from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company, Storage, Supplier, Product, Supply, SupplyProduct, Sale, ProductSale


# =============================================================================
# Mixin для фильтрации данных по компании пользователя
# =============================================================================
class CompanyFilterMixin:
    """
    Миксин для фильтрации объектов по компании пользователя.
    Не-суперпользователи видят только объекты своих компаний.
    """
    
    def get_queryset(self, request):
        """Фильтрация queryset по компаниям пользователя"""
        qs = super().get_queryset(request)
        
        # Суперпользователь видит всё
        if request.user.is_superuser:
            return qs
        
        # Получаем компании, к которым привязан пользователь
        user_companies = request.user.get_companies()
        
        # Если компаний нет — возвращаем пустой queryset
        if not user_companies.exists():
            return qs.none()
        
        # owner компании
        owner_companies = Company.objects.filter(owner=request.user)
        
        # Компании, где пользователь в списке users
        member_companies = user_companies.filter(users=request.user)
        
        # Объединяем — видим компании где мы владелец ИЛИ участник
        visible_companies = owner_companies | member_companies
        
        return qs.filter(company__in=visible_companies.distinct())
    
    def get_form(self, request, obj=None, **kwargs):
        """Фильтрация поля company в формах"""
        form = super().get_form(request, obj, **kwargs)
        
        # Для не-суперпользователей фильтруем выбор компании
        if hasattr(form.base_fields, 'company') and not request.user.is_superuser:
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            form.base_fields['company'].queryset = visible_companies.distinct()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        """Проверка права на просмотр"""
        if request.user.is_superuser:
            return True
        
        # Если объект не указан — разрешаем просмотр списка
        if obj is None:
            return True
        
        # Проверяем принадлежность компании
        if hasattr(obj, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.company in visible_companies.distinct()
        
        return True
    
    def has_change_permission(self, request, obj=None):
        """Проверка права на изменение"""
        if request.user.is_superuser:
            return True
        
        if obj is None:
            return True
        
        if hasattr(obj, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.company in visible_companies.distinct()
        
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Проверка права на удаление"""
        if request.user.is_superuser:
            return True
        
        if obj is None:
            return True
        
        if hasattr(obj, 'company'):
            # Только владелец может удалять
            return obj.company.owner == request.user
        
        return True
    
    def has_add_permission(self, request):
        """Проверка права на создание"""
        if request.user.is_superuser:
            return True
        
        # Staff-пользователь может добавлять ТОЛЬКО если у него уже есть компания
        if request.user.is_staff:
            has_company = request.user.get_companies().exists()
            return has_company  # True если компания есть, False если нет
        
        return False


# =============================================================================
# User Admin
# =============================================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админка пользователей с дополнительными полями для CRM.
    """
    list_display = ['email', 'first_name', 'last_name', 'is_company_owner', 
                    'is_staff', 'is_active', 'get_companies_display']
    list_filter = ['is_staff', 'is_active', 'is_company_owner', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Поля для отображения в списке
    def get_companies_display(self, obj):
        """Отображение компаний пользователя"""
        companies = obj.get_companies()
        if companies.exists():
            return ", ".join([c.name for c in companies[:3]])
        return "-"
    get_companies_display.short_description = 'Компании'
    get_companies_display.admin_order_field = 'email'
    
    def get_queryset(self, request):
        """Суперпользователь видит всех, остальные — только свой аккаунт"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(pk=request.user.pk)
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Пользователь может видеть только себя
        if obj:
            return obj == request.user
        return True
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Пользователь может менять только себя (не staff статусы)
        if obj:
            return obj == request.user
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Только суперпользователь может удалять
        return request.user.is_superuser


# =============================================================================
# Company Admin
# =============================================================================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'inn', 'owner', 'get_users_count', 'created']
    search_fields = ['name', 'inn']
    filter_horizontal = ['users']
    readonly_fields = ['created']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Получаем компании, где пользователь владелец или участник
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = Company.objects.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        
        # Если компаний нет - всё равно возвращаем queryset (пустой, но не None)
        # Это позволяет Django показать пустую страницу вместо ошибки
        return visible_companies.distinct()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Для staff-пользователей без компании можно создать новую
            # Ограничиваем owner только собой
            form.base_fields['owner'].queryset = User.objects.filter(pk=request.user.pk)
        return form
    
    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Участников'
    
    def has_view_permission(self, request, obj=None):
        # Всегда разрешаем просмотр списка компаний (staff и выше)
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            # Разрешаем доступ к списку для staff
            return request.user.is_staff
        # Только владелец может изменять компанию
        return obj.owner == request.user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Разрешаем создание компании владельцам или если её ещё нет"""
        if request.user.is_superuser:
            return True
        
        # Для staff-пользователей или владельцев компаний
        if request.user.is_staff or request.user.is_company_owner:
            # Проверяем, есть ли уже компания у пользователя как владельца
            existing_company = Company.objects.filter(owner=request.user).exists()
            # Если компании нет - можно создать
            return not existing_company
        
        return False


# =============================================================================
# Storage Admin
# =============================================================================
@admin.register(Storage)
class StorageAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ['company', 'address', 'get_products_count']
    search_fields = ['address', 'company__name']
    
    def get_products_count(self, obj):
        return obj.products.count()
    get_products_count.short_description = 'Товаров'


# =============================================================================
# Supplier Admin
# =============================================================================
@admin.register(Supplier)
class SupplierAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ['name', 'company', 'contact_info', 'get_supplies_count']
    search_fields = ['name', 'contact_info', 'company__name']
    list_filter = ['company']
    
    def get_supplies_count(self, obj):
        return obj.supplies.count()
    get_supplies_count.short_description = 'Поставок'


# =============================================================================
# Product Admin
# =============================================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'purchase_price', 'quantity', 'storage', 'get_company']
    search_fields = ['title', 'description', 'storage__company__name']
    list_filter = ['storage__company']
    
    def get_company(self, obj):
        return obj.storage.company.name
    get_company.short_description = 'Компания'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        user_companies = request.user.get_companies()
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = user_companies.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        
        # Product связан с Company через storage
        return qs.filter(storage__company__in=visible_companies.distinct())
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.storage.company in visible_companies.distinct()
        return True
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.storage.company in visible_companies.distinct()
        return True
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            return obj.storage.company.owner == request.user
        return True
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            has_company = request.user.get_companies().exists()
            return has_company
        return False


# =============================================================================
# Supply Admin
# =============================================================================
@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'storage', 'delivery_date', 'get_company', 'get_total_quantity']
    list_filter = ['supplier', 'storage', 'delivery_date']
    search_fields = ['supplier__name', 'storage__company__name']
    readonly_fields = ['delivery_date']
    
    def get_company(self, obj):
        return obj.storage.company.name
    get_company.short_description = 'Компания'
    
    def get_total_quantity(self, obj):
        total = sum(sp.quantity for sp in obj.supply_products.all())
        return total
    get_total_quantity.short_description = 'Всего товаров'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        user_companies = request.user.get_companies()
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = user_companies.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        
        # Supply связан с Company через storage
        return qs.filter(storage__company__in=visible_companies.distinct())
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.storage.company in visible_companies.distinct()
        return True
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            user_companies = request.user.get_companies()
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = user_companies.filter(users=request.user)
            visible_companies = owner_companies | member_companies
            return obj.storage.company in visible_companies.distinct()
        return True
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(obj, 'storage') and hasattr(obj.storage, 'company'):
            return obj.storage.company.owner == request.user
        return True
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            has_company = request.user.get_companies().exists()
            return has_company
        return False


# =============================================================================
# SupplyProduct Admin
# =============================================================================
@admin.register(SupplyProduct)
class SupplyProductAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ['supply', 'product', 'quantity']
    list_filter = ['supply']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Фильтруем через supply → storage → company
        user_companies = request.user.get_companies()
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = user_companies.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        return qs.filter(supply__storage__company__in=visible_companies.distinct())


# =============================================================================
# Sale Admin
# =============================================================================
@admin.register(Sale)
class SaleAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ['id', 'buyer_name', 'company', 'sale_date', 'total_amount', 'get_items_count']
    list_filter = ['company', 'sale_date']
    search_fields = ['buyer_name', 'company__name']
    readonly_fields = ['total_amount']
    inlines = []
    
    def get_items_count(self, obj):
        return obj.product_sales.count()
    get_items_count.short_description = 'Позиций'
    
    def get_form(self, request, obj=None, **kwargs):
        """Фильтрация компании в форме"""
        form = super().get_form(request, obj, **kwargs)
        
        if hasattr(form.base_fields, 'company') and not request.user.is_superuser:
            owner_companies = Company.objects.filter(owner=request.user)
            member_companies = request.user.get_companies().filter(users=request.user)
            visible_companies = owner_companies | member_companies
            form.base_fields['company'].queryset = visible_companies.distinct()
        
        return form


# =============================================================================
# ProductSale Admin
# =============================================================================
@admin.register(ProductSale)
class ProductSaleAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'price']
    list_filter = ['sale']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Фильтруем через sale → company
        user_companies = request.user.get_companies()
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = user_companies.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        return qs.filter(sale__company__in=visible_companies.distinct())


# =============================================================================
# Inline для Sale в ProductSale
# =============================================================================
class ProductSaleInline(admin.TabularInline):
    model = ProductSale
    extra = 1
    readonly_fields = ['product', 'quantity', 'price']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_companies = request.user.get_companies()
        owner_companies = Company.objects.filter(owner=request.user)
        member_companies = user_companies.filter(users=request.user)
        visible_companies = owner_companies | member_companies
        return qs.filter(sale__company__in=visible_companies.distinct())


# Обновляем SaleAdmin с inline
SaleAdmin.inlines = [ProductSaleInline]
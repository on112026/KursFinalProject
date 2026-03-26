"""
Custom middleware for CRMLite application.
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


class PermissionDeniedMiddleware:
    """
    Middleware для обработки ошибок PermissionDenied в Django Admin.
    Показывает информативную страницу с объяснением причин отказа в доступе.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Обрабатывает исключение PermissionDenied.
        Возвращает кастомную страницу с информацией о причинах отказа.
        """
        if isinstance(exception, PermissionDenied):
            # Проверяем, что это запрос к админке
            if request.path.startswith('/admin/'):
                return self._render_permission_denied(request)
        
        return None
    
    def _render_permission_denied(self, request):
        """
        Рендерит кастомную страницу ошибки 403.
        """
        user = request.user
        
        # Определяем, может ли пользователь создать компанию
        can_create_company = False
        if user.is_authenticated:
            if user.is_superuser:
                can_create_company = True
            elif (user.is_staff or user.is_company_owner) and not user.get_companies().filter(owner=user).exists():
                can_create_company = True
        
        # Определяем, есть ли у пользователя доступ к каким-либо компаниям
        has_company_access = False
        if user.is_authenticated:
            has_company_access = user.get_companies().exists()
        
        context = {
            'can_create_company': can_create_company,
            'has_company_access': has_company_access,
            'user': user,
        }
        
        return render(request, 'admin/permission_denied.html', context, status=403)
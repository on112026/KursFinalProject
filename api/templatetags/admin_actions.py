from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('admin_actions/available_actions.html')
def available_actions(user):
    """
    Возвращает список доступных действий для пользователя в админке.
    """
    actions = {
        'api_docs': [],
        'create_company': [],
        'company': [],
        'storage': [],
        'suppliers': [],
        'products': [],
        'supplies': [],
        'sales': [],
        'user_management': [],
    }
    
    base_api_url = '/api/'
    
    # API документация доступна всем staff-пользователям
    if user.is_staff:
        actions['api_docs'] = [
            {
                'title': 'Swagger UI',
                'url': f'{base_api_url}swagger/',
                'description': 'Интерактивная документация API',
                'icon': '📖'
            },
            {
                'title': 'ReDoc',
                'url': f'{base_api_url}redoc/',
                'description': 'Документация API в формате ReDoc',
                'icon': '📄'
            },
            {
                'title': 'JSON Schema',
                'url': f'{base_api_url}schema/',
                'description': 'JSON схема API',
                'icon': '📋'
            },
        ]
    
    # Проверяем наличие компании у пользователя
    from api.models import Company
    company = None
    if hasattr(user, 'company') and user.company:
        company = user.company
    else:
        company = Company.objects.filter(users=user).first()
    
    # Все авторизованные пользователи без компании видят кнопку создания компании
    if not company and user.is_authenticated:
        # Проверяем, может ли пользователь создать компанию (владелец, не имеющий компании)
        can_create_company = user.is_staff or user.is_superuser
        if can_create_company:
            actions['create_company'] = [
                {
                    'title': 'Создать компанию',
                    'url': '/admin/api/company/add/',
                    'description': 'Создайте свою компанию для начала работы с CRM системой',
                    'icon': '🏢',
                    'api_url': f'{base_api_url}company/create/',
                    'api_method': 'POST',
                },
            ]
    
    # Все staff-пользователи с компанией получают базовые действия
    if company:
        # Проверяем, является ли пользователь владельцем компании
        is_owner = company.owner == user
        
        # Действия с компанией
        actions['company'] = [
            {
                'title': 'Просмотр компании',
                'url': '/admin/api/company/',
                'description': 'Информация о компании',
                'icon': '🏢',
                'api_url': f'{base_api_url}company/',
                'api_method': 'GET',
            },
        ]
        
        if is_owner:
            actions['company'].extend([
                {
                    'title': 'Редактирование компании',
                    'url': f'/admin/api/company/{company.id}/change/',
                    'description': 'Изменить данные компании',
                    'icon': '✏️',
                    'api_url': f'{base_api_url}company/update/',
                    'api_method': 'PUT',
                },
            ])
        
        # Действия с API для компании
        actions['company'].extend([
            {
                'title': 'Информация о компании (API)',
                'url': f'{base_api_url}company/',
                'description': 'Получить данные компании через API',
                'icon': '🔗',
                'api_url': f'{base_api_url}company/',
                'api_method': 'GET',
            },
        ])
        
        # Проверяем наличие склада
        has_storage = hasattr(company, 'storage') and company.storage
        
        if is_owner:
            actions['storage'] = [
                {
                    'title': 'Создать склад',
                    'url': '/admin/api/storage/add/',
                    'description': 'Создать новый склад для компании',
                    'icon': '➕',
                    'api_url': f'{base_api_url}storage/create/',
                    'api_method': 'POST',
                },
            ]
        
        if has_storage:
            storage = company.storage
            actions['storage'].extend([
                {
                    'title': 'Просмотр склада',
                    'url': f'/admin/api/storage/{storage.id}/change/',
                    'description': f'Склад: {storage.address}',
                    'icon': '📦',
                    'api_url': f'{base_api_url}storage/',
                    'api_method': 'GET',
                },
            ])
            
            if is_owner:
                actions['storage'].extend([
                    {
                        'title': 'Редактирование склада',
                        'url': f'/admin/api/storage/{storage.id}/change/',
                        'description': 'Изменить данные склада',
                        'icon': '✏️',
                        'api_url': f'{base_api_url}storage/update/{storage.id}/',
                        'api_method': 'PUT',
                    },
                    {
                        'title': 'Удаление склада',
                        'url': f'/admin/api/storage/{storage.id}/delete/',
                        'description': 'Удалить склад',
                        'icon': '🗑️',
                        'api_url': f'{base_api_url}storage/delete/{storage.id}/',
                        'api_method': 'DELETE',
                    },
                ])
        
        # Поставщики (доступны всем участникам компании)
        actions['suppliers'] = [
            {
                'title': 'Список поставщиков',
                'url': '/admin/api/supplier/',
                'description': 'Просмотр всех поставщиков компании',
                'icon': '🚚',
                'api_url': f'{base_api_url}suppliers/',
                'api_method': 'GET',
            },
        ]
        
        if is_owner:
            actions['suppliers'].extend([
                {
                    'title': 'Добавить поставщика',
                    'url': '/admin/api/supplier/add/',
                    'description': 'Создать нового поставщика',
                    'icon': '➕',
                    'api_url': f'{base_api_url}suppliers/',
                    'api_method': 'POST',
                },
            ])
        
        # Товары (доступны всем участникам компании)
        if has_storage:
            actions['products'] = [
                {
                    'title': 'Список товаров',
                    'url': '/admin/api/product/',
                    'description': 'Просмотр всех товаров на складе',
                    'icon': '📋',
                    'api_url': f'{base_api_url}products/',
                    'api_method': 'GET',
                },
            ]
            
            if is_owner:
                actions['products'].extend([
                    {
                        'title': 'Добавить товар',
                        'url': '/admin/api/product/add/',
                        'description': 'Создать новый товар',
                        'icon': '➕',
                        'api_url': f'{base_api_url}products/',
                        'api_method': 'POST',
                    },
                ])
            
            # Поставки
            actions['supplies'] = [
                {
                    'title': 'Список поставок',
                    'url': '/admin/api/supply/',
                    'description': 'Просмотр всех поставок',
                    'icon': '📥',
                    'api_url': f'{base_api_url}supplies/',
                    'api_method': 'GET',
                },
            ]
            
            if is_owner:
                actions['supplies'].extend([
                    {
                        'title': 'Создать поставку',
                        'url': '/admin/api/supply/add/',
                        'description': 'Оформить новую поставку товаров',
                        'icon': '📦',
                        'api_url': f'{base_api_url}supplies/create/',
                        'api_method': 'POST',
                    },
                ])
        
        # Продажи (доступны всем участникам компании)
        actions['sales'] = [
            {
                'title': 'Список продаж',
                'url': '/admin/api/sale/',
                'description': 'Просмотр всех продаж',
                'icon': '💰',
                'api_url': f'{base_api_url}sales/',
                'api_method': 'GET',
            },
        ]
        
        if is_owner:
            actions['sales'].extend([
                {
                    'title': 'Создать продажу',
                    'url': '/admin/api/sale/add/',
                    'description': 'Оформить новую продажу',
                    'icon': '🛒',
                    'api_url': f'{base_api_url}sales/create/',
                    'api_method': 'POST',
                },
            ])
        
        # Управление пользователями (только для владельца)
        if is_owner:
            actions['user_management'] = [
                {
                    'title': 'Привязать пользователя к компании',
                    'url': '#',
                    'description': 'Добавить пользователя к компании',
                    'icon': '👥',
                    'api_url': f'{base_api_url}company/attach-user/',
                    'api_method': 'POST',
                },
            ]
    
    # Суперпользователь видит всех пользователей
    if user.is_superuser:
        actions['user_management'].insert(0, {
            'title': 'Все пользователи',
            'url': '/admin/auth/user/',
            'description': 'Управление пользователями системы',
            'icon': '👤',
        })
    
    # Убираем пустые категории
    return {k: v for k, v in actions.items() if v}
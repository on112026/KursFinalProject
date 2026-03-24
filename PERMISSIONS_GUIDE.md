# Система прав доступа в Django Admin

## Обзор

Данный проект реализует систему прав доступа в Django Admin, где пользователи видят и управляют только данными своих компаний.

## Исправленная проблема: Staff-пользователи без компании

### Симптомы
После регистрации через API и входа в админку (`/admin/`) новый пользователь видел сообщение:
```
Site administration
You don't have permission to view or edit anything.
```

### Причина
1. При регистрации через API (`RegisterView`) пользователю устанавливается `is_staff = True`
2. Но у нового пользователя нет компании
3. В `CompanyAdmin.get_queryset()` для не-суперпользователей без компании возвращался пустой queryset
4. Django показывал сообщение об отсутствии прав

### Решение
Изменения в `CompanyAdmin` (`api/admin.py`):

```python
def has_view_permission(self, request, obj=None):
    # Разрешаем просмотр списка для всех staff-пользователей
    if request.user.is_superuser or request.user.is_staff:
        return True
    return False

def has_add_permission(self, request):
    if request.user.is_superuser:
        return True
    # Для staff-пользователей разрешаем создание компании если её нет
    if request.user.is_staff:
        existing_company = Company.objects.filter(owner=request.user).exists()
        return not existing_company
    return False
```

Также при создании компании через API устанавливается `is_company_owner = True`:
```python
# В CreateCompanyView
company = serializer.save(owner=request.user)
request.user.is_company_owner = True
request.user.save()
```

### Результат
- Staff-пользователь без компании видит пустую страницу с кнопкой "Add Company"
- После создания компании пользователь может работать с данными
- Владельцы компаний видят свои компании в списке

## Права пользователей

### Флаги пользователя

| Флаг | Описание |
|------|----------|
| `is_staff = True` | Позволяет входить в админку (`/admin/`) |
| `is_superuser = True` | Полные права на все данные (игнорирует проверки) |
| `is_active = True` | Аккаунт активен |
| `is_company_owner = True` | Является владельцем компании |

### Что даёт `is_staff = True`?

✅ **Может:**
- Входить на страницу `/admin/`
- Видеть главную страницу админки
- Видеть модели, на которые есть permissions

❌ **Не может автоматически:**
- Просматривать данные
- Создавать объекты
- Изменять объекты
- Удалять объекты

Для полноценной работы нужно назначить **permissions** или сделать пользователя **суперпользователем**.

---

## Архитектура системы прав

### 1. Методы в модели User (`models.py`)

```python
def get_companies(self):
    """Возвращает компании, к которым имеет доступ пользователь"""
    # Компании где он владелец ИЛИ участник
    owner_companies = Company.objects.filter(owner=self)
    member_companies = Company.objects.filter(users=self)
    return owner_companies | member_companies

def can_access_company(self, company):
    """Проверяет доступ к конкретной компании"""
    return company.owner == self or company.users.filter(pk=self.pk).exists()
```

### 2. CompanyFilterMixin (`admin.py`)

Миксин для фильтрации данных в админке:

```python
class CompanyFilterMixin:
    def get_queryset(self, request):
        # Суперпользователь видит всё
        if request.user.is_superuser:
            return qs
        # Обычные пользователи видят только свои компании
        return qs.filter(company__in=request.user.get_companies())
    
    def has_view_permission(self, request, obj=None):
        # Проверка: принадлежит ли объект компании пользователя
        
    def has_change_permission(self, request, obj=None):
        # Проверка: может ли изменять объект
        
    def has_delete_permission(self, request, obj=None):
        # Только владелец компании может удалять
        return obj.company.owner == request.user
    
    def has_add_permission(self, request):
        # Может создавать, если есть доступные компании
```

---

## Уровни доступа

### 1. Суперпользователь (`is_superuser = True`)
```
✅ Полный доступ ко всем данным
✅ Может управлять пользователями
✅ Может управлять всеми компаниями
✅ Может удалять любые объекты
```

### 2. Владелец компании
```
✅ Видит свою компанию в списке
✅ Может управлять сотрудниками компании
✅ Может создавать/изменять/удалять товары, поставки, продажи
✅ Может удалять компанию (только через суперпользователя)
```

### 3. Сотрудник компании (в списке `users`)
```
✅ Видит компанию в списке
✅ Может просматривать товары, поставки, продажи
✅ Может создавать новые товары, поставки, продажи
✅ Может изменять товары, поставки, продажи
❌ НЕ может удалять компании
❌ НЕ может управлять сотрудниками
❌ НЕ может удалять объекты (только владелец)
```

---

## Как работает фильтрация

### Пример: SaleAdmin

```
Запрос: GET /admin/api/sale/
        
┌─────────────────────────────────────────────────────────────┐
│  Пользователь: manager@company.ru                           │
│  Компании: ["ООО Ромашка"] (где он участник)                │
├─────────────────────────────────────────────────────────────┤
│  SQL запрос:                                                │
│  SELECT * FROM sale                                        │
│  WHERE company_id IN (                                      │
│      SELECT id FROM company                                │
│      WHERE owner_id = user_id                              │
│      OR id IN (SELECT company_id FROM company_users        │
│                WHERE user_id = user_id)                     │
│  )                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Добавление нового пользователя с правами

### Через Django Shell:

```python
from api.models import User, Company

# Создать пользователя
user = User.objects.create_user(
    email='manager@company.ru',
    password='securepassword123',
    first_name='Иван',
    last_name='Петров'
)

# Добавить is_staff для доступа в админку
user.is_staff = True
user.save()

# Привязать к компании
company = Company.objects.get(name='ООО Ромашка')
company.users.add(user)
```

### Через админку (суперпользователь):

1. Зайти в `/admin/`
2. Перейти в **Users** → создать/редактировать
3. Установить `is_staff = True`
4. В **Компания** → **User permissions** добавить в нужную компанию

---

## Права на уровне моделей

| Модель | Владелец компании | Сотрудник |
|--------|-------------------|-----------|
| Company | View, Change | View |
| Storage | Full | Full |
| Supplier | Full | Full |
| Product | Full | Full |
| Supply | Full | Full |
| Sale | Full | Full |
| ProductSale | Full | Full |

---

## Расширение системы прав

### Добавление роли "Менеджер продаж"

```python
# В models.py
class User(AbstractUser):
    # ... существующие поля ...
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('salesman', 'Продавец'),
    ], default='manager')

# В admin.py
class SaleAdmin(CompanyFilterMixin, admin.ModelAdmin):
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # Только менеджеры и админы могут создавать продажи
        return request.user.role in ['admin', 'manager']
```

---

## Troubleshooting

### Пользователь не видит данные в админке

1. Проверить `is_staff = True`
2. Проверить, что пользователь добавлен в компанию
3. Проверить `is_superuser = True` (для тестирования)

### Ошибка "Permission denied"

```python
# Проверить в shell:
from api.models import User
user = User.objects.get(email='test@example.com')
print(user.get_companies())  # Должен показать компании
```

### Пользователь видит чужие компании

```python
# Проверить связи:
company = Company.objects.get(name='Компания')
print(company.owner)  # Должен быть владелец
print(company.users.all())  # Должны быть только сотрудники
```

---

## Команды для управления

```bash
# Создать суперпользователя
python manage.py createsuperuser

# Открыть shell
python manage.py shell

# Применить миграции
python manage.py migrate

# Создать миграцию
python manage.py makemigrations
# Описание проекта CRMLite

## Общая информация
CRMLite — это Django REST API CRM система для управления компаниями, пользователями, складами, поставщиками, товарами и продажами. Система обеспечивает полный цикл работы: от создания компании до оформления продаж с автоматическим контролем остатков.

## Основные компоненты

### 1. Модель данных

#### Пользователь (User)
```python
- email: str (уникальный, используется для входа)
- first_name, last_name: str
- is_company_owner: bool
- Компании: OneToOne к Company (если владелец)
- Компании-участник: ManyToMany к Company
```

#### Компания (Company)
```python
- inn: str (уникальный ИНН)
- name: str
- owner: User (OneToOne)
- users: ManyToMany User (сотрудники)
- storage: OneToOne Storage (опционально)
- suppliers: Related Suppliers
- sales: Related Sales
```

#### Склад (Storage)
```python
- address: str
- company: Company (OneToOne)
- products: Related Products
- supplies: Related Supplies
```

#### Поставщик (Supplier)
```python
- name: str
- inn: str (опционально)
- contact_info: str
- company: Company (ForeignKey)
- supplies: Related Supplies
```

#### Товар (Product)
```python
- title: str
- description: str
- purchase_price: Decimal (цена закупки)
- sale_price: Decimal (цена продажи)
- quantity: int (остаток на складе)
- storage: Storage (ForeignKey)
```

#### Поставка (Supply)
```python
- supplier: Supplier (ForeignKey)
- storage: Storage (ForeignKey)
- delivery_date: datetime
- supply_products: Related SupplyProducts
```

#### Поставка-Товар (SupplyProduct)
```python
- supply: Supply (ForeignKey)
- product: Product (ForeignKey)
- quantity: int
```

#### Продажа (Sale)
```python
- company: Company (ForeignKey)
- buyer_name: str
- sale_date: datetime
- total_amount: Decimal
- product_sales: Related ProductSales
```

#### Продажа-Товар (ProductSale)
```python
- sale: Sale (ForeignKey)
- product: Product (ForeignKey)
- quantity: int
- price: Decimal (цена в момент продажи)
```

### 2. Аутентификация
- **JWT токены**: Access (60 мин) + Refresh
- **Регистрация**: Открытая регистрация новых пользователей
- **Вход**: Аутентификация по email и паролю

## Функциональность

### Управление пользователями
- Регистрация новых пользователей
- Аутентификация с JWT токенами
- Управление профилем пользователя
- Привязка к компании как сотрудник

### Управление компаниями
- Создание компаний (один владелец — одна компания)
- Редактирование информации о компании
- Удаление компаний (каскадное удаление связанных данных)
- Проверка уникальности ИНН
- Прикрепление сотрудников к компании
- Удаление сотрудников из компании

### Управление складами
- Создание складов для компаний (одна компания — один склад)
- Редактирование адреса склада
- Удаление складов
- Привязка к конкретной компании

### Управление поставщиками
- Создание поставщиков
- Редактирование информации о поставщиках
- Удаление поставщиков
- Привязка к компании (владелец и сотрудники видят поставщиков)

### Управление товарами
- Создание товаров (всегда с quantity = 0)
- Редактирование названия, описания, цен
- Нельзя изменять quantity напрямую (только через поставки)
- Удаление товаров
- Привязка к складу компании

### Управление поставками
- Создание поставки товаров от поставщика
- Автоматическое увеличение quantity товаров
- Валидация: только положительные количества
- Проверка принадлежности товара компании

### Управление продажами
- Создание продажи (выбор товаров и количества)
- Автоматическое списание quantity товаров
- Контроль остатков (нельзя продать больше, чем есть)
- Расчет total_amount по ценам продажи
- Пагинация списка продаж
- Фильтрация по дате (date_from, date_to)
- Обновление только buyer_name и sale_date
- Удаление продажи возвращает товары на склад

## API Эндпоинты

### Аутентификация
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/api/register/` | Регистрация | `{email, password, first_name, last_name}` |
| POST | `/api/login/` | Вход | `{email, password}` |

### Компании
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/api/company/create/` | Создание компании | `{name, inn}` |
| GET | `/api/company/` | Получение компании | — |
| PUT | `/api/company/update/` | Полное обновление | `{name, inn}` |
| PATCH | `/api/company/update/` | Частичное обновление | `{name}` |
| DELETE | `/api/company/delete/` | Удаление компании | — |

### Сотрудники (только владелец)
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/api/company/attach-user/` | Прикрепить | `{user_id}` или `{email}` |
| GET | `/api/company/employees/` | Список | — |
| DELETE | `/api/company/employees/<id>/` | Удалить | — |

### Склады
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/api/storage/create/` | Создание | `{address}` |
| GET | `/api/storage/` | Получение | — |
| GET | `/api/storage/<id>/` | По ID | — |
| PUT | `/api/storage/update/<id>/` | Полное обновление | `{address}` |
| PATCH | `/api/storage/update/<id>/` | Частичное обновление | `{address}` |
| DELETE | `/api/storage/delete/<id>/` | Удаление | — |

### Поставщики
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| GET | `/api/suppliers/` | Список | — |
| POST | `/api/suppliers/` | Создание | `{name, inn, contact_info}` |
| GET | `/api/suppliers/<id>/` | По ID | — |
| PUT | `/api/suppliers/<id>/` | Полное обновление | `{name, inn, contact_info}` |
| PATCH | `/api/suppliers/<id>/` | Частичное обновление | `{name}` |
| DELETE | `/api/suppliers/<id>/` | Удаление | — |

### Товары
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| GET | `/api/products/` | Список | — |
| POST | `/api/products/` | Создание | `{title, description, purchase_price, sale_price}` |
| GET | `/api/products/<id>/` | По ID | — |
| PUT | `/api/products/<id>/` | Обновление | `{title, description, purchase_price, sale_price}` |
| PATCH | `/api/products/<id>/` | Частичное обновление | `{title}` |
| DELETE | `/api/products/<id>/` | Удаление | — |

### Поставки
| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| GET | `/api/supplies/` | Список | — |
| POST | `/api/supplies/create/` | Создание | `[{id, quantity, supplier_id}]` |

### Продажи
| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/api/sales/` | Список | `?page=1&page_size=10&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` |
| POST | `/api/sales/create/` | Создание | `{buyer_name, product_sales: [{product, quantity}]}` |
| GET | `/api/sales/<id>/` | По ID | — |
| PUT | `/api/sales/<id>/` | Обновление | `{buyer_name, sale_date}` |
| PATCH | `/api/sales/<id>/` | Частичное обновление | `{buyer_name}` |
| DELETE | `/api/sales/<id>/` | Удаление (возврат на склад) | — |

## Примеры запросов (curl)

### Регистрация нового пользователя
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!", "first_name": "Имя", "last_name": "Фамилия"}'
```

**Ответ:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "is_company_owner": false
  }
}
```

### Вход в систему
```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

### Создание компании
```bash
curl -X POST http://127.0.0.1:8000/api/company/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "ООО Ромашка", "inn": "123456789012"}'
```

**Ответ:**
```json
{"id":1,"inn":"123456789012","name":"ООО Ромашка","owner":1}
```

### Создание склада
```bash
curl -X POST http://127.0.0.1:8000/api/storage/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"address": "ул. Складская, д.1"}'
```

### Создание поставщика
```bash
curl -X POST http://127.0.0.1:8000/api/suppliers/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Поставщик ООО", "inn": "987654321098", "contact_info": "supplier@example.com"}'
```

### Создание товара
```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"title": "Товар А", "description": "Описание товара", "purchase_price": 100.00, "sale_price": 150.00}'
```

**Ответ (quantity всегда 0):**
```json
{"id":1,"title":"Товар А","description":"Описание товара","purchase_price":"100.00","sale_price":"150.00","quantity":0}
```

### Создание поставки (пополнение остатков)
```bash
curl -X POST http://127.0.0.1:8000/api/supplies/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '[{"id": 1, "quantity": 100, "supplier_id": 1}]'
```

**Ответ:**
```json
{
  "id": 1,
  "supplier_name": "Поставщик ООО",
  "delivery_date": "2026-03-26T10:00:00Z",
  "products": [{"id": 1, "title": "Товар А", "quantity": 100}]
}
```

### Создание продажи
```bash
curl -X POST http://127.0.0.1:8000/api/sales/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"buyer_name": "Иванов Иван", "product_sales": [{"product": 1, "quantity": 5}]}'
```

**Ответ:**
```json
{
  "id": 1,
  "buyer_name": "Иванов Иван",
  "sale_date": "2026-03-26T10:05:00Z",
  "total_amount": "750.00",
  "product_sales": [{"id": 1, "product": 1, "quantity": 5, "price": "150.00"}]
}
```

### Прикрепление сотрудника
```bash
curl -X POST http://127.0.0.1:8000/api/company/attach-user/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"email": "employee@example.com"}'
```

### Получение списка продаж с фильтрацией
```bash
curl "http://127.0.0.1:8000/api/sales/?date_from=2026-01-01&date_to=2026-12-31&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Ответ (с пагинацией):**
```json
{
  "count": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [...]
}
```

## Безопасность

### Управление доступом
- **JWT аутентификация** для всех защищенных эндпоинтов
- **Владелец компании**: полный доступ (CRUD)
- **Сотрудники**: чтение (компания, склады, товары, продажи) + создание продаж
- **Валидация данных** через сериализаторы

### Ограничения бизнес-логики
| Ограничение | Описание |
|-------------|----------|
| Одна компания на владельца | Нельзя создать вторую компанию |
| Один склад на компанию | Нельзя создать второй склад |
| Только владелец управляет компанией | Сотрудники не могут изменять |
| Только владелец управляет сотрудниками | attach-user, delete employee |
| quantity только через поставки | Нельзя изменить quantity напрямую |
| Достаточно остатков для продажи | Нельзя продать больше чем есть |
| Удаление продажи возвращает на склад | Товары восстанавливаются |

## Технические характеристики

### Стек технологий
| Компонент | Версия |
|-----------|--------|
| Django | 6.0.3 |
| Django REST Framework | 3.17.0 |
| Simple JWT | 5.5.1 |
| drf-spectacular | 0.29.0 |
| Python | 3.8+ |

### Конфигурация
- **Режим**: DEBUG (dev) / False (prod)
- **База данных**: SQLite (dev) / PostgreSQL (prod)
- **Временная зона**: UTC

## Описание работы проекта

### Полный цикл работы

1. **Регистрация и вход**
   - Пользователь регистрируется через `/api/register/`
   - Получает JWT токены (access + refresh)
   - Использует access token для доступа к API

2. **Создание компании**
   - Аутентифицированный пользователь создает компанию
   - Компания привязывается как владелец
   - `is_company_owner` становится True

3. **Управление сотрудниками**
   - Владелец прикрепляет пользователей к компании
   - Сотрудники получают доступ к чтению и продажам

4. **Управление складом**
   - Владелец создает склад для компании
   - Склад привязывается к компании

5. **Работа с товарами**
   - Создание поставщиков
   - Создание товаров (quantity = 0)
   - Создание поставок (увеличивает quantity)
   - Редактирование товаров (цены, название)

6. **Оформление продаж**
   - Создание продажи списывает quantity
   - Рассчитывается total_amount
   - Удаление продажи возвращает товары

## Тесты

Проект включает комплексный набор тестов в `api/test_api.py`:

### Категории тестов
| Категория | Описание |
|-----------|----------|
| AuthenticationTests | Регистрация, вход, валидация |
| CompanyTests | CRUD компаний, ограничения |
| StorageTests | CRUD складов |
| SupplierTests | CRUD поставщиков |
| ProductTests | CRUD товаров, валидация quantity |
| SupplyTests | Создание поставок, валидация |
| SaleTests | Продажи, пагинация, фильтры |
| EmployeeManagementTests | attach/detach сотрудников |
| AccessControlTests | Права владельца vs сотрудника |
| IntegrationTests | Полные сценарии использования |

### Запуск тестов
```bash
python manage.py test api.test_api
```

## Документация API

- **Swagger UI**: http://127.0.0.1:8000/api/swagger
- **Redoc**: http://127.0.0.1:8000/api/redoc
- **Schema JSON**: http://127.0.0.1:8000/api/schema/
- **Schema YAML**: http://127.0.0.1:8000/api/schema/yaml/

## Развертывание

### Разработка
- Локальный сервер: `python manage.py runserver`
- SQLite база данных
- Режим DEBUG

### Продакшн
1. Настроить `SECRET_KEY` в settings.py
2. Настроить `ALLOWED_HOSTS`
3. Настроить PostgreSQL
4. Использовать HTTPS
5. Собрать статические файлы: `python manage.py collectstatic`
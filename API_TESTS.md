# API Тесты - CRMLite

Документация всех протестированных эндпоинтов с примерами запросов и ответов.

## Настройка окружения

```bash
cd FinalProject02
source venv/bin/activate
python manage.py runserver
```

## Тестовые пользователи

- **Суперпользователь (админка):** admin@example.com / admin123
- **Владелец компании:** owner@test.com / TestPass123!
- **Прикреплённый пользователь:** user2@test.com / TestPass123!

---

## 1. Регистрация пользователя

### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@test.com", "password": "TestPass123!", "first_name": "Owner", "last_name": "Test"}'
```

### Ответ:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 3,
    "username": "owner@test.com",
    "email": "owner@test.com",
    "first_name": "Owner",
    "last_name": "Test",
    "is_company_owner": false
  }
}
```

---

## 2. Создание компании

### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/company/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Test Company LLC", "inn": "123456789012"}'
```

### Ответ:
```json
{
  "id": 2,
  "inn": "123456789012",
  "name": "Test Company LLC",
  "owner": 3
}
```

---

## 3. Создание склада

### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/storage/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"address": "ул. Складская, д.1", "name": "Main Storage"}'
```

### Ответ:
```json
{
  "id": 2,
  "address": "ул. Складская, д.1",
  "company": 2
}
```

---

## 4. Поставщики (Suppliers)

### 4.1 Создание поставщика

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/suppliers/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Supplier ABC", "contact_info": "contact@supplier.com"}'
```

#### Ответ:
```json
{
  "id": 1,
  "name": "Supplier ABC",
  "contact_info": "contact@supplier.com",
  "company": 2
}
```

### 4.2 Получение списка поставщиков

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/suppliers/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```json
[
  {
    "id": 1,
    "name": "Supplier ABC",
    "contact_info": "contact@supplier.com",
    "company": 2
  }
]
```

### 4.3 Получение поставщика по ID

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/suppliers/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```json
{
  "id": 1,
  "name": "Supplier ABC",
  "contact_info": "contact@supplier.com",
  "company": 2
}
```

### 4.4 Обновление поставщика

#### Запрос:
```bash
curl -X PUT http://127.0.0.1:8000/api/suppliers/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Updated Supplier", "contact_info": "new@supplier.com"}'
```

#### Ответ:
```json
{
  "id": 1,
  "name": "Updated Supplier",
  "contact_info": "new@supplier.com",
  "company": 2
}
```

### 4.5 Удаление поставщика

#### Запрос:
```bash
curl -X DELETE http://127.0.0.1:8000/api/suppliers/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```
HTTP 204 No Content
```

---

## 5. Товары (Products)

### 5.1 Создание товара (quantity = 0)

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"title": "Product 1", "description": "Test product", "purchase_price": 1200.00}'
```

#### Ответ:
```json
{
  "id": 1,
  "title": "Product 1",
  "description": "Test product",
  "purchase_price": "1200.00",
  "quantity": 0,
  "storage": 2
}
```

### 5.2 Получение списка товаров

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```json
[
  {
    "id": 1,
    "title": "Product 1",
    "description": "Test product",
    "purchase_price": "1200.00",
    "quantity": 10
  },
  {
    "id": 2,
    "title": "Product 2",
    "description": "Second test product",
    "purchase_price": "500.00",
    "quantity": 5
  }
]
```

### 5.3 Получение товара по ID

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/products/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```json
{
  "id": 1,
  "title": "Product 1",
  "description": "Test product",
  "purchase_price": "1200.00",
  "quantity": 10,
  "storage": 2
}
```

### 5.4 Обновление товара (quantity нельзя изменить)

#### Запрос:
```bash
curl -X PUT http://127.0.0.1:8000/api/products/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"title": "Product 1 Updated", "quantity": 999}'
```

#### Ответ (quantity остаётся без изменений):
```json
{
  "id": 1,
  "title": "Product 1 Updated",
  "description": "Test product",
  "purchase_price": "1200.00",
  "quantity": 10,
  "storage": 2
}
```

### 5.5 Удаление товара

#### Запрос:
```bash
curl -X DELETE http://127.0.0.1:8000/api/products/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```
HTTP 204 No Content
```

---

## 6. Поставки (Supplies)

### 6.1 Создание поставки (увеличивает quantity товаров)

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/supplies/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '[{"id": 1, "quantity": 10, "supplier_id": 1}, {"id": 2, "quantity": 5, "supplier_id": 1}]'
```

#### Ответ:
```json
{
  "id": 1,
  "supplier_name": "Supplier ABC",
  "date": "2026-03-22T19:15:41.452021Z",
  "products": [
    {"product__id": 1, "product__title": "Product 1", "quantity": 10},
    {"product__id": 2, "product__title": "Product 2", "quantity": 5}
  ]
}
```

### 6.2 Получение списка поставок

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/supplies/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Ответ:
```json
[
  {
    "id": 1,
    "supplier_name": "Supplier ABC",
    "date": "2026-03-22T19:15:41.452021Z"
  }
]
```

### 6.3 Проверка: отрицательное количество отклоняется

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/supplies/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '[{"id": 1, "quantity": -5, "supplier_id": 1}]'
```

#### Ответ:
```json
{
  "error": "All quantities must be positive integers"
}
```

---

## 7. Прикрепление пользователя к компании

### 7.1 Прикрепление пользователя (только владелец)

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/company/attach-user/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"user_id": 4}'
```

#### Ответ:
```json
{
  "message": "User user2@test.com has been attached to company Test Company LLC"
}
```

### 7.2 Прикреплённый пользователь видит товары компании

#### Запрос:
```bash
curl -X GET http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer ATTACHED_USER_ACCESS_TOKEN"
```

#### Ответ:
```json
[
  {
    "id": 1,
    "title": "Product 1 Updated",
    "description": "Test product",
    "purchase_price": "1200.00",
    "quantity": 10
  },
  {
    "id": 2,
    "title": "Product 2",
    "description": "Second test product",
    "purchase_price": "500.00",
    "quantity": 5
  }
]
```

### 7.3 Прикреплённый пользователь создаёт товар

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ATTACHED_USER_ACCESS_TOKEN" \
  -d '{"title": "Product 3", "description": "Created by attached user", "purchase_price": 800.00}'
```

#### Ответ:
```json
{
  "id": 3,
  "title": "Product 3",
  "description": "Created by attached user",
  "purchase_price": "800.00",
  "quantity": 0,
  "storage": 2
}
```

---

## 8. Ошибки доступа

### 8.1 Запрос без токена

#### Запрос:
```bash
curl http://127.0.0.1:8000/api/company/
```

#### Ответ:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 8.2 Попытка прикрепить себя

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/company/attach-user/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"user_id": 3}'
```

#### Ответ:
```json
{
  "error": "Cannot attach yourself"
}
```

### 8.3 Прикреплённый пользователь (не владелец) не может прикреплять других

#### Запрос:
```bash
curl -X POST http://127.0.0.1:8000/api/company/attach-user/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ATTACHED_USER_ACCESS_TOKEN" \
  -d '{"user_id": 5}'
```

#### Ответ:
```json
{
  "error": "User has no company"
}
```

---

## Итоговые тестовые данные

После выполнения всех тестов:

| ID | Название | quantity | purchase_price |
|----|----------|----------|----------------|
| 1 | Product 1 Updated | 10 | 1200.00 |
| 2 | Product 2 | 5 | 500.00 |
| 3 | Product 3 | 0 | 800.00 |

| ID | Поставщик | Компания |
|----|-----------|----------|
| 2 | New Supplier | Test Company LLC |

| ID | Поставщик | Дата |
|----|-----------|------|
| 1 | Supplier ABC | 2026-03-22T19:15:41Z |
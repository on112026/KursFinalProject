# Описание проекта CRMLite

## Общая информация
CRMLite - это Django REST API CRM система, предназначенная для управления компаниями, пользователями и складами. Система использует современные технологии и обеспечивает безопасный доступ через JWT аутентификацию.

## Основные компоненты

### 1. Модель данных
- **Пользователь (User)**: Расширенная модель Django с email-аутентификацией
- **Компания (Company)**: Сущность с ИНН и владельцем
- **Склад (Storage)**: Физическое хранилище, связанное с компанией

### 2. Аутентификация
- **JWT токены**: Доступные на 60 минут, обновляемые
- **Регистрация**: Открытая регистрация новых пользователей
- **Вход**: Аутентификация по email и паролю

## Функциональность

### Управление пользователями
- Регистрация новых пользователей
- Аутентификация с JWT токенами
- Управление профилем пользователя

### Управление компаниями
- Создание компаний (только для владельцев)
- Редактирование информации о компании
- Удаление компаний
- Проверка уникальности ИНН

### Управление складами
- Создание складов для компаний
- Редактирование информации о складах
- Удаление складов
- Привязка к конкретной компании

## API Эндпоинты

### Пользователи
- `POST /api/register/` - Регистрация нового пользователя
- `POST /api/login/` - Вход в систему

### Компании
- `POST /api/company/create/` - Создание компании
- `GET /api/company/` - Получение компании
- `PUT /api/company/update/` - Редактирование компании
- `DELETE /api/company/delete/` - Удаление компании

### Склады
- `POST /api/storage/create/` - Создание склада
- `GET /api/storage/` - Получение склада
- `GET /api/storage/{id}/` - Получение склада по ID
- `PUT /api/storage/update/{id}/` - Редактирование склада
- `DELETE /api/storage/delete/{id}/` - Удаление склада

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
    "username": "user@example.com",
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

### Доступ без токена (ожидаемый отказ)
```bash
curl http://127.0.0.1:8000/api/company/
```

**Ответ:**
```json
{"detail":"Authentication credentials were not provided."}
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

### Ограничение: одна компания на пользователя
```bash
curl -X POST http://127.0.0.1:8000/api/company/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Вторая компания", "inn": "987654321098"}'
```

**Ответ:**
```json
{"error":"User already has a company"}
```

### Обновление компании
```bash
curl -X PUT http://127.0.0.1:8000/api/company/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Обновленное название компании"}'
```

### Создание склада
```bash
curl -X POST http://127.0.0.1:8000/api/storage/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Основной склад", "address": "ул. Складская, д.1", "capacity": 1000}'
```

**Ответ:**
```json
{"id":1,"address":"ул. Складская, д.1","company":1}
```

### Ограничение: один склад на компанию
```bash
curl -X POST http://127.0.0.1:8000/api/storage/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Второй склад", "address": "ул. Пушкина, д.10", "capacity": 500}'
```

**Ответ:**
```json
{"error":"Company already has a storage"}
```

### Получение склада по ID
```bash
curl http://127.0.0.1:8000/api/storage/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Обновление склада
```bash
curl -X PUT http://127.0.0.1:8000/api/storage/update/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"address": "ул. Новая, д.5", "capacity": 2000}'
```

### Удаление склада
```bash
curl -X DELETE http://127.0.0.1:8000/api/storage/delete/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Удаление компании
```bash
curl -X DELETE http://127.0.0.1:8000/api/company/delete/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Безопасность

### Управление доступом
- **JWT аутентификация** для всех защищенных эндпоинтов
- **Права доступа** на основе владения компанией
- **Валидация данных** через сериализаторы

### Ограничения
- Пользователь может иметь только одну компанию
- Компания может иметь только одно хранилище
- Только владелец компании может управлять ею
- Только владелец может управлять хранилищем

## Технические характеристики

### Стек технологий
- **Backend**: Django 6.0.3
- **API Framework**: Django REST Framework
- **Аутентификация**: Simple JWT
- **Документация**: drf-spectacular
- **База данных**: SQLite

### Конфигурация
- **Режим**: DEBUG
- **Секретный ключ**: Настроен для разработки
- **Временная зона**: UTC

## Описание работы проекта

### Регистрация и вход
1. Пользователь регистрируется через `/api/register/`
2. Получает JWT токены (доступ и обновление)
3. Использует токен для доступа к защищенным эндпоинтам

### Управление компанией
1. Аутентифицированный пользователь создает компанию
2. Компания привязывается к пользователю как владелец
3. Владелец может управлять компанией и ее хранилищем

### Управление складом
1. Владелец компании создает склад
2. Склад привязывается к компании
3. Владелец может управлять информацией о складе

## Документация

### API документация
- Доступна через Swagger UI
- Автоматически генерируется из кода
- Включает все эндпоинты и модели

### Админ-панель
- Django админ-панель для управления данными
- Доступна для суперпользователей
- Интуитивно понятный интерфейс

## Развертывание

### Разработка
- Локальный сервер разработки
- SQLite база данных
- Режим DEBUG

### Продакшн
- Необходима настройка SECRET_KEY
- Настройка ALLOWED_HOSTS
- Использование HTTPS

## Поддержка

### Требования к системе
- Python 3.8+
- 512MB+ оперативной памяти
- 100MB+ дискового пространства

## Лицензия
Проект доступен под открытой лицензией, позволяющей модификацию и распространение.
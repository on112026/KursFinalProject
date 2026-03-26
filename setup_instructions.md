# Инструкция по настройке и запуску проекта CRMLite

## Предварительные требования
- Python 3.8 или выше
- Git (опционально, для клонирования репозитория)
- PostgreSQL (опционально, для продакшена)

## Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/on112026/KursFinalProject.git
cd KursFinalProject
```

## Шаг 2: Создание виртуального окружения
Создайте виртуальное окружение для изоляции зависимостей проекта:

```bash
python3 -m venv venv
```

## Шаг 3: Активация виртуального окружения

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

## Шаг 4: Установка зависимостей
Установите все необходимые пакеты из файла `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Шаг 5: Настройка базы данных

### Для разработки (SQLite)
```bash
python manage.py migrate
```

### Для продакшена (PostgreSQL)
1. Создайте базу данных PostgreSQL:
```sql
CREATE DATABASE crmlite_db;
CREATE USER crmlite_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE crmlite_db TO crmlite_user;
```

2. Обновите настройки в `crmlite/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crmlite_db',
        'USER': 'crmlite_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. Примените миграции:
```bash
python manage.py migrate
```

## Шаг 6: Создание суперпользователя (опционально)
Для доступа к админ-панели создайте суперпользователя:

```bash
python manage.py createsuperuser
```

## Шаг 7: Запуск сервера разработки
Запустите Django сервер:

```bash
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

## Доступные ресурсы

| Ресурс | URL |
|--------|-----|
| API эндпоинты | http://127.0.0.1:8000/api/ |
| Swagger UI | http://127.0.0.1:8000/api/swagger/ |
| Redoc | http://127.0.0.1:8000/api/redoc/ |
| Админ-панель | http://127.0.0.1:8000/admin/ |

## Запуск тестов

```bash
# Все тесты
python manage.py test api.test_api

# Конкретная категория тестов
python manage.py test api.test_api.AuthenticationTests
python manage.py test api.test_api.CompanyTests
python manage.py test api.test_api.SaleTests
```

### Категории тестов
- `AuthenticationTests` — Регистрация, вход, валидация
- `CompanyTests` — CRUD компаний, ограничения
- `StorageTests` — CRUD складов
- `SupplierTests` — CRUD поставщиков
- `ProductTests` — CRUD товаров, валидация quantity
- `SupplyTests` — Создание поставок
- `SaleTests` — Продажи, пагинация, фильтры
- `EmployeeManagementTests` — Прикрепление/удаление сотрудников
- `AccessControlTests` — Права доступа
- `IntegrationTests` — Интеграционные сценарии

## Полезные команды Django

```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Проверка конфигурации
python manage.py check

# Создание суперпользователя
python manage.py createsuperuser

# Django shell
python manage.py shell

# Сбор статических файлов
python manage.py collectstatic
```

## Примеры использования API

### Регистрация пользователя
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "first_name": "Иван", "last_name": "Иванов"}'
```

### Вход в систему
```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Создание компании
```bash
curl -X POST http://127.0.0.1:8000/api/company/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "ООО Компания", "inn": "123456789012"}'
```

### Создание склада
```bash
curl -X POST http://127.0.0.1:8000/api/storage/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"address": "г. Москва, ул. Примерная, д. 1"}'
```

## Конфигурация для продакшена

### 1. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```bash
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgres://user:password@localhost:5432/crmlite_db
```

### 2. Обновление settings.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
```

### 3. Использование HTTPS
Рекомендуется использовать Nginx/Apache с SSL сертификатом:
- Let's Encrypt для бесплатных сертификатов
- Redirect HTTP → HTTPS

### 4. Gunicorn/WSGI сервер
```bash
pip install gunicorn
gunicorn crmlite.wsgi:application --bind 0.0.0.0:8000
```

## Устранение проблем

### Ошибка при установке зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Порт занят
```bash
# Найти процесс на порту 8000
lsof -i :8000  # Linux
netstat -tulpn | grep :8000  # Linux

# Использовать другой порт
python manage.py runserver 8001
```

### Проблемы с миграциями
```bash
python manage.py migrate --fake-initial
```

### Ошибка подключения к PostgreSQL
```bash
# Проверьте, что PostgreSQL запущен
sudo systemctl status postgresql  # Linux

# Или установите пароль для пользователя
psql -U postgres -c "ALTER USER postgres PASSWORD 'your_password';"
```

## Важные примечания

- **JWT токены**: Действительны 60 минут, используйте refresh token для обновления
- **Одна компания**: Пользователь может владеть только одной компанией
- **Один склад**: Компания может иметь только один склад
- **Контроль остатков**: Количество товаров изменяется только через поставки и продажи
- **Безопасность**: Не храните SECRET_KEY в коде, используйте переменные окружения

## Завершение работы

Деактивация виртуального окружения:
```bash
deactivate
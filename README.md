# CRMLite

Django REST API CRM система для управления компаниями, пользователями и складами с JWT аутентификацией.

## Возможности

- **Пользователи**: регистрация, аутентификация, управление профилем
- **Компании**: создание, редактирование, удаление (ИНН, владелец)
- **Склады**: управление хранилищами с привязкой к компаниям
- **Безопасность**: JWT токены (60 мин), права доступа

## Быстрый старт

```bash
git clone https://github.com/on112026/FinalProject02.git
cd FinalProject02
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py runserver
```

## Документация

- **[Инструкция по установке](setup_instructions.md)** — детальная настройка, запуск, команды
- **[Описание проекта](project_description.md)** — полное API, примеры curl, безопасность

## API эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/register/` | Регистрация |
| POST | `/api/login/` | Вход |
| POST | `/api/company/create/` | Создание компании |
| GET/PUT/DELETE | `/api/company/` | Управление компанией |
| POST | `/api/storage/create/` | Создание склада |
| GET/PUT/DELETE | `/api/storage/` | Управление складом |

## Доступ

- API: http://127.0.0.1:8000/api
- Swagger UI: http://127.0.0.1:8000/api/swagger
- Redoc: http://127.0.0.1:8000/api/redoc
- Admin: http://127.0.0.1:8000/admin/
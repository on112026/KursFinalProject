from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Company, Storage

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            inn='1234567890',
            name='Test Company',
            owner=self.user
        )
        self.storage = Storage.objects.create(
            address='123 Test Address',
            company=self.company
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self.token.access_token}'

    def test_register(self):
        response = self.client.post('/api/register/', {
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        response = self.client.post('/api/login/', {
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_create_company(self):
        response = self.client.post('/api/company/create/', {
            'inn': '1234567890',
            'name': 'Test Company'
        })
        self.assertEqual(response.status_code, 400)

    def test_get_company(self):
        self.test_create_company()
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, 200)

    def test_create_storage(self):
        self.test_create_company()
        response = self.client.post('/api/storage/create/', {
            'address': '123 Test Street'
        })
        self.assertEqual(response.status_code, 400)

    def test_get_storage(self):
        self.test_create_storage()
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, 200)

    def test_register_and_create_company(self):
        """Тест: регистрация → получение токенов → создание компании"""
        # Регистрация нового пользователя
        response = self.client.post('/api/register/', {
            'email': 'newuser_reg@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что получили токены
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        access_token = response.json()['access']
        
        # Создаём компанию с использованием полученного токена
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/company/create/', {
            'inn': '9876543210',
            'name': 'New Test Company'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['name'], 'New Test Company')
        self.assertEqual(response.json()['inn'], '9876543210')

    def test_login_and_create_storage(self):
        """Тест: логин → получение токенов → создание склада"""
        # Логин
        response = self.client.post('/api/login/', {
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что получили токены
        self.assertIn('access', response.json())
        access_token = response.json()['access']
        
        # Удаляем существующий склад (чтобы создать новый)
        self.storage.delete()
        
        # Создаём склад с использованием полученного токена
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/storage/create/', {
            'address': '456 New Storage Address'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['address'], '456 New Storage Address')

    def test_full_workflow(self):
        """Тест полного сценария: регистрация → компания → склад"""
        # 1. Регистрация
        response = self.client.post('/api/register/', {
            'email': 'workflow@example.com',
            'password': 'workflow123',
            'first_name': 'Workflow',
            'last_name': 'Test'
        })
        self.assertEqual(response.status_code, 201)
        access_token = response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 2. Создание компании
        response = self.client.post('/api/company/create/', {
            'inn': '111222333444',
            'name': 'Workflow Company LLC'
        })
        self.assertEqual(response.status_code, 201)
        company_id = response.json()['id']
        
        # 3. Создание склада
        response = self.client.post('/api/storage/create/', {
            'address': '789 Workflow Street, Office 100'
        })
        self.assertEqual(response.status_code, 201)
        storage_id = response.json()['id']
        
        # 4. Проверяем получение компании
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], company_id)
        
        # 5. Проверяем получение склада
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], storage_id)
        
        # 6. Проверяем получение склада по ID
        response = self.client.get(f'/api/storage/{storage_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['address'], '789 Workflow Street, Office 100')

from django.test import TestCase, Client
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Company, Storage

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
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
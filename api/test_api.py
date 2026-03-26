"""
Comprehensive API Tests for CRMLite Project
Tests all API endpoints using Django REST Framework's test client.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    User, Company, Storage, Supplier, Product,
    Supply, SupplyProduct, Sale, ProductSale
)


class BaseAPITestCase(TestCase):
    """Base test case with common setup for all API tests"""

    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()

        # Create owner user
        self.owner = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='ownerpass123',
            first_name='Owner',
            last_name='User'
        )

        # Create regular user (employee)
        self.employee = User.objects.create_user(
            username='employee@example.com',
            email='employee@example.com',
            password='employeepass123',
            first_name='Employee',
            last_name='User'
        )

        # Create another user to be attached to company
        self.new_user = User.objects.create_user(
            username='newuser@example.com',
            email='newuser@example.com',
            password='newuserpass123',
            first_name='New',
            last_name='User'
        )

        # Create company owned by owner
        self.company = Company.objects.create(
            inn='123456789012',
            name='Test Company LLC',
            owner=self.owner
        )

        # Create storage for company
        self.storage = Storage.objects.create(
            address='123 Main Street, City',
            company=self.company
        )

        # Create owner tokens
        self.owner_token = RefreshToken.for_user(self.owner)
        self.owner_access_token = str(self.owner_token.access_token)

        # Create supplier
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            inn='987654321098',
            contact_info='supplier@example.com',
            company=self.company
        )

        # Create product
        self.product = Product.objects.create(
            title='Test Product',
            description='Test product description',
            purchase_price=100.00,
            sale_price=150.00,
            quantity=50,
            storage=self.storage
        )

        # Create second product
        self.product2 = Product.objects.create(
            title='Second Product',
            description='Second product description',
            purchase_price=200.00,
            sale_price=300.00,
            quantity=30,
            storage=self.storage
        )

    def authenticate_as_owner(self):
        """Set authentication header for owner"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_access_token}')

    def authenticate_as_employee(self):
        """Set authentication header for employee and attach to company"""
        self.company.users.add(self.employee)
        # Employee needs to be able to access storage through get_user_company
        # which checks Company.objects.filter(users=user).first()
        self.employee_token = RefreshToken.for_user(self.employee)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.employee_token.access_token}')

    def authenticate_as_new_user(self):
        """Set authentication header for new user"""
        self.new_user_token = RefreshToken.for_user(self.new_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.new_user_token.access_token}')


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

class AuthenticationTests(BaseAPITestCase):

    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post('/api/register/', {
            'email': 'registertest@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'registertest@example.com')

    def test_register_duplicate_email(self):
        """Test registration with existing email fails"""
        response = self.client.post('/api/register/', {
            'email': 'owner@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Test registration with missing fields fails"""
        response = self.client.post('/api/register/', {
            'email': 'incomplete@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/api/login/', {
            'email': 'owner@example.com',
            'password': 'ownerpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'owner@example.com')

    def test_login_wrong_password(self):
        """Test login with wrong password fails"""
        response = self.client.post('/api/login/', {
            'email': 'owner@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent email fails"""
        response = self.client.post('/api/login/', {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Test login with missing fields fails"""
        response = self.client.post('/api/login/', {
            'email': 'owner@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# COMPANY TESTS
# =============================================================================

class CompanyTests(BaseAPITestCase):

    def test_create_company_success(self):
        """Test successful company creation"""
        self.authenticate_as_new_user()
        response = self.client.post('/api/company/create/', {
            'inn': '999988887777',
            'name': 'New Company LLC'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Company LLC')
        self.assertEqual(response.data['inn'], '999988887777')

        # Verify user is marked as company owner
        self.new_user.refresh_from_db()
        self.assertTrue(self.new_user.is_company_owner)

    def test_create_company_duplicate_inn(self):
        """Test company creation with duplicate INN fails"""
        self.authenticate_as_new_user()
        response = self.client.post('/api/company/create/', {
            'inn': '123456789012',  # Same INN as existing company
            'name': 'Duplicate INN Company'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_company_already_has_company(self):
        """Test creating second company fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/company/create/', {
            'inn': '999988887777',
            'name': 'Second Company'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_company_success(self):
        """Test getting company info"""
        self.authenticate_as_owner()
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Company LLC')
        self.assertEqual(response.data['inn'], '123456789012')

    def test_get_company_employee_access(self):
        """Test employee can get company info"""
        self.authenticate_as_employee()
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_company_no_company(self):
        """Test getting company when user has none"""
        self.authenticate_as_new_user()
        response = self.client.get('/api/company/')
        # User has no company, so get_user_company returns None -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_company_put_success(self):
        """Test full company update with PUT"""
        self.authenticate_as_owner()
        response = self.client.put('/api/company/update/', {
            'inn': '123456789012',
            'name': 'Updated Company Name'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Company Name')

    def test_update_company_patch_success(self):
        """Test partial company update with PATCH"""
        self.authenticate_as_owner()
        response = self.client.patch('/api/company/update/', {
            'name': 'Patched Company Name'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Patched Company Name')

    def test_update_company_not_owner(self):
        """Test employee cannot update company - returns 404 because get_user_company check fails"""
        self.authenticate_as_employee()
        response = self.client.patch('/api/company/update/', {
            'name': 'Unauthorized Update'
        })
        # Employee is attached via M2M, but UpdateCompanyView uses request.user.company
        # which doesn't exist for employees (only OneToOne for owner)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_company_success(self):
        """Test company deletion by owner"""
        self.authenticate_as_owner()
        response = self.client.delete('/api/company/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify company is deleted
        self.assertFalse(Company.objects.filter(id=self.company.id).exists())

    def test_delete_company_not_owner(self):
        """Test employee cannot delete company - returns 404 because get_user_company check fails"""
        self.authenticate_as_employee()
        response = self.client.delete('/api/company/delete/')
        # Employee is attached via M2M, but DeleteCompanyView uses request.user.company
        # which doesn't exist for employees (only OneToOne for owner)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# STORAGE TESTS
# =============================================================================

class StorageTests(BaseAPITestCase):

    def test_create_storage_success(self):
        """Test successful storage creation"""
        # First create new company without storage
        self.authenticate_as_new_user()
        self.client.post('/api/company/create/', {
            'inn': '111122223333',
            'name': 'Storage Test Company'
        })

        response = self.client.post('/api/storage/create/', {
            'address': '456 New Storage Address'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['address'], '456 New Storage Address')

    def test_create_storage_company_already_has_storage(self):
        """Test creating second storage fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/storage/create/', {
            'address': 'Another Storage'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_storage_success(self):
        """Test getting storage info"""
        self.authenticate_as_owner()
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], '123 Main Street, City')

    def test_get_storage_by_id_success(self):
        """Test getting storage by ID"""
        self.authenticate_as_owner()
        response = self.client.get(f'/api/storage/{self.storage.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], '123 Main Street, City')

    def test_get_storage_by_id_not_found(self):
        """Test getting nonexistent storage"""
        self.authenticate_as_owner()
        response = self.client.get('/api/storage/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_storage_put_success(self):
        """Test full storage update with PUT"""
        self.authenticate_as_owner()
        response = self.client.put(f'/api/storage/update/{self.storage.id}/', {
            'address': '789 Updated Address'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], '789 Updated Address')

    def test_update_storage_patch_success(self):
        """Test partial storage update with PATCH"""
        self.authenticate_as_owner()
        response = self.client.patch(f'/api/storage/update/{self.storage.id}/', {
            'address': 'Patch Updated Address'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Patch Updated Address')

    def test_update_storage_not_owner(self):
        """Test employee cannot update storage"""
        self.authenticate_as_employee()
        response = self.client.patch(f'/api/storage/update/{self.storage.id}/', {
            'address': 'Unauthorized'
        })
        # UpdateStorageView checks storage.company.owner != request.user
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_storage_success(self):
        """Test storage deletion by owner"""
        self.authenticate_as_owner()
        response = self.client.delete(f'/api/storage/delete/{self.storage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify storage is deleted
        self.assertFalse(Storage.objects.filter(id=self.storage.id).exists())

    def test_delete_storage_not_owner(self):
        """Test employee cannot delete storage"""
        self.authenticate_as_employee()
        response = self.client.delete(f'/api/storage/delete/{self.storage.id}/')
        # DeleteStorageView checks storage.company.owner != request.user
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =============================================================================
# SUPPLIER TESTS
# =============================================================================

class SupplierTests(BaseAPITestCase):

    def test_list_suppliers(self):
        """Test listing all suppliers"""
        self.authenticate_as_owner()
        response = self.client.get('/api/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_suppliers_empty(self):
        """Test listing suppliers when none exist"""
        # Create new company without suppliers
        self.authenticate_as_new_user()
        self.client.post('/api/company/create/', {
            'inn': '444455556666',
            'name': 'No Suppliers Company'
        })

        response = self.client.get('/api/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_supplier_success(self):
        """Test successful supplier creation"""
        self.authenticate_as_owner()
        response = self.client.post('/api/suppliers/', {
            'name': 'New Supplier',
            'inn': '555566667777',
            'contact_info': 'new@supplier.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Supplier')

    def test_get_supplier_success(self):
        """Test getting supplier by ID"""
        self.authenticate_as_owner()
        response = self.client.get(f'/api/suppliers/{self.supplier.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Supplier')

    def test_get_supplier_not_found(self):
        """Test getting nonexistent supplier"""
        self.authenticate_as_owner()
        response = self.client.get('/api/suppliers/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_supplier_put_success(self):
        """Test full supplier update with PUT"""
        self.authenticate_as_owner()
        response = self.client.put(f'/api/suppliers/{self.supplier.id}/', {
            'name': 'Updated Supplier',
            'inn': '111122223333',
            'contact_info': 'updated@supplier.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Supplier')

    def test_update_supplier_patch_success(self):
        """Test partial supplier update with PATCH"""
        self.authenticate_as_owner()
        response = self.client.patch(f'/api/suppliers/{self.supplier.id}/', {
            'name': 'Patched Supplier'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Patched Supplier')

    def test_delete_supplier_success(self):
        """Test supplier deletion"""
        self.authenticate_as_owner()
        response = self.client.delete(f'/api/suppliers/{self.supplier.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify supplier is deleted
        self.assertFalse(Supplier.objects.filter(id=self.supplier.id).exists())


# =============================================================================
# PRODUCT TESTS
# =============================================================================

class ProductTests(BaseAPITestCase):

    def test_list_products(self):
        """Test listing all products"""
        self.authenticate_as_owner()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_products_empty(self):
        """Test listing products when none exist"""
        # Create new company without products
        self.authenticate_as_new_user()
        self.client.post('/api/company/create/', {
            'inn': '777788889999',
            'name': 'Empty Products Company'
        })
        self.client.post('/api/storage/create/', {
            'address': 'No Products Storage'
        })

        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_product_success(self):
        """Test successful product creation (quantity = 0)"""
        self.authenticate_as_owner()
        response = self.client.post('/api/products/', {
            'title': 'New Product',
            'description': 'New product desc',
            'purchase_price': 50.00,
            'sale_price': 80.00
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Product')
        self.assertEqual(response.data['quantity'], 0)  # Must be 0

    def test_create_product_no_storage(self):
        """Test product creation fails without storage - returns 404 because user has no storage"""
        self.authenticate_as_new_user()
        self.client.post('/api/company/create/', {
            'inn': '888899990000',
            'name': 'No Storage Company'
        })
        # Don't create storage, so get_user_company returns company but without storage

        response = self.client.post('/api/products/', {
            'title': 'No Storage Product',
            'purchase_price': 50.00,
            'sale_price': 80.00
        })
        # ProductListCreateView checks if company.storage exists, returns 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_product_success(self):
        """Test getting product by ID"""
        self.authenticate_as_owner()
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Product')

    def test_get_product_not_found(self):
        """Test getting nonexistent product"""
        self.authenticate_as_owner()
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_put_success(self):
        """Test full product update with PUT"""
        self.authenticate_as_owner()
        response = self.client.put(f'/api/products/{self.product.id}/', {
            'title': 'Updated Product',
            'description': 'Updated desc',
            'purchase_price': 120.00,
            'sale_price': 180.00
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Product')

    def test_update_product_quantity_forbidden(self):
        """Test that quantity cannot be updated directly"""
        self.authenticate_as_owner()
        response = self.client.put(f'/api/products/{self.product.id}/', {
            'title': 'Product with quantity',
            'quantity': 100  # This should be ignored
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 50)  # Original quantity

    def test_delete_product_success(self):
        """Test product deletion"""
        self.authenticate_as_owner()
        response = self.client.delete(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify product is deleted
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())


# =============================================================================
# SUPPLY TESTS
# =============================================================================

class SupplyTests(BaseAPITestCase):

    def test_list_supplies_empty(self):
        """Test listing supplies when none exist"""
        self.authenticate_as_owner()
        response = self.client.get('/api/supplies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_supply_success(self):
        """Test successful supply creation"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': 10,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['supplier_name'], 'Test Supplier')
        self.assertEqual(len(response.data['products']), 1)

        # Verify product quantity increased
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 60)  # 50 + 10

    def test_create_supply_multiple_products(self):
        """Test supply creation with multiple products"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': 10,
                'supplier_id': self.supplier.id
            },
            {
                'id': self.product2.id,
                'quantity': 5,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['products']), 2)

    def test_create_supply_empty_list(self):
        """Test supply creation with empty list fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_supply_negative_quantity(self):
        """Test supply creation with negative quantity fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': -5,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_supply_zero_quantity(self):
        """Test supply creation with zero quantity fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': 0,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_supply_product_not_found(self):
        """Test supply creation with nonexistent product fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': 99999,
                'quantity': 10,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_supply_no_supplier(self):
        """Test supply creation without supplier_id fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': 10
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# EMPLOYEE MANAGEMENT TESTS
# =============================================================================

class EmployeeManagementTests(BaseAPITestCase):

    def test_attach_user_by_id(self):
        """Test attaching user to company by ID"""
        self.authenticate_as_owner()
        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.new_user.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify user is attached
        self.assertTrue(self.company.users.filter(id=self.new_user.id).exists())

    def test_attach_user_by_email(self):
        """Test attaching user to company by email"""
        self.authenticate_as_owner()
        response = self.client.post('/api/company/attach-user/', {
            'email': 'newuser@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_attach_self_forbidden(self):
        """Test attaching yourself to your own company fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.owner.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attach_already_attached(self):
        """Test attaching already attached user fails"""
        self.authenticate_as_owner()
        self.company.users.add(self.new_user)

        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.new_user.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attach_user_not_owner(self):
        """Test non-owner cannot attach users - returns 404 because employee has no company via owner path"""
        self.authenticate_as_employee()
        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.new_user.id
        })
        # AttachUserToCompanyView checks request.user.company
        # which doesn't exist for employees (only OneToOne for owner)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_employees(self):
        """Test listing company employees"""
        self.authenticate_as_owner()
        self.company.users.add(self.employee, self.new_user)

        response = self.client.get('/api/company/employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_employees_empty(self):
        """Test listing employees when none attached"""
        self.authenticate_as_owner()
        response = self.client.get('/api/company/employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_delete_employee(self):
        """Test removing employee from company"""
        self.authenticate_as_owner()
        self.company.users.add(self.employee)

        response = self.client.delete(f'/api/company/employees/{self.employee.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify employee is removed
        self.assertFalse(self.company.users.filter(id=self.employee.id).exists())

    def test_delete_employee_not_owner(self):
        """Test non-owner cannot delete employees - returns 404 because employee has no company"""
        self.authenticate_as_employee()
        response = self.client.delete(f'/api/company/employees/{self.new_user.id}/')
        # EmployeeDeleteView checks request.user.company
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_owner_forbidden(self):
        """Test cannot remove owner from company"""
        self.authenticate_as_owner()
        response = self.client.delete(f'/api/company/employees/{self.owner.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# SALE TESTS
# =============================================================================

class SaleTests(BaseAPITestCase):

    def test_list_sales_empty(self):
        """Test listing sales when none exist"""
        self.authenticate_as_owner()
        response = self.client.get('/api/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_sale_success(self):
        """Test successful sale creation"""
        self.authenticate_as_owner()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'John Doe',
            'product_sales': [
                {
                    'product': self.product.id,
                    'quantity': 5
                }
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['buyer_name'], 'John Doe')
        self.assertEqual(response.data['total_amount'], '750.00')  # 150 * 5
        self.assertEqual(len(response.data['product_sales']), 1)

        # Verify product quantity decreased
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 45)  # 50 - 5

    def test_create_sale_multiple_products(self):
        """Test sale creation with multiple products"""
        self.authenticate_as_owner()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Jane Smith',
            'product_sales': [
                {'product': self.product.id, 'quantity': 2},
                {'product': self.product2.id, 'quantity': 3}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['product_sales']), 2)
        # Total: 150*2 + 300*3 = 300 + 900 = 1200

    def test_create_sale_insufficient_quantity(self):
        """Test sale creation with insufficient stock fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'No Stock Buyer',
            'product_sales': [
                {'product': self.product.id, 'quantity': 1000}  # More than available
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Not enough quantity', response.data['error'])

    def test_create_sale_empty_products(self):
        """Test sale creation without products fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Empty Buyer',
            'product_sales': []
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_sale_product_not_found(self):
        """Test sale creation with nonexistent product fails"""
        self.authenticate_as_owner()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Ghost Buyer',
            'product_sales': [
                {'product': 99999, 'quantity': 1}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_sale_success(self):
        """Test getting sale by ID"""
        self.authenticate_as_owner()
        # Create a sale first
        sale = Sale.objects.create(
            company=self.company,
            buyer_name='Test Buyer',
            sale_date=timezone.now(),
            total_amount=300.00
        )
        ProductSale.objects.create(
            sale=sale,
            product=self.product,
            quantity=2,
            price=150.00
        )

        response = self.client.get(f'/api/sales/{sale.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['buyer_name'], 'Test Buyer')

    def test_get_sale_not_found(self):
        """Test getting nonexistent sale"""
        self.authenticate_as_owner()
        response = self.client.get('/api/sales/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_sales_pagination(self):
        """Test sales list pagination"""
        self.authenticate_as_owner()
        # Create multiple sales
        for i in range(15):
            sale = Sale.objects.create(
                company=self.company,
                buyer_name=f'Buyer {i}',
                sale_date=timezone.now(),
                total_amount=100.00
            )
            ProductSale.objects.create(
                sale=sale,
                product=self.product,
                quantity=1,
                price=100.00
            )

        # Test default pagination (page 1, 10 items)
        response = self.client.get('/api/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 10)

        # Test second page
        response = self.client.get('/api/sales/?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        # Test custom page size
        response = self.client.get('/api/sales/?page_size=5')
        self.assertEqual(len(response.data['results']), 5)

    def test_list_sales_date_filter(self):
        """Test sales list date filtering"""
        self.authenticate_as_owner()

        # Create sales with different dates
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        sale_today = Sale.objects.create(
            company=self.company, buyer_name='Today Buyer',
            sale_date=today, total_amount=100
        )
        sale_yesterday = Sale.objects.create(
            company=self.company, buyer_name='Yesterday Buyer',
            sale_date=yesterday, total_amount=200
        )
        sale_last_week = Sale.objects.create(
            company=self.company, buyer_name='Last Week Buyer',
            sale_date=last_week, total_amount=300
        )

        for sale in [sale_today, sale_yesterday, sale_last_week]:
            ProductSale.objects.create(
                sale=sale, product=self.product, quantity=1, price=100
            )

        # Filter from yesterday - should include yesterday and today (2 sales)
        response = self.client.get(f'/api/sales/?date_from={yesterday.strftime("%Y-%m-%d")}')
        self.assertEqual(response.data['count'], 2)

        # Filter to yesterday - API uses date_to + 1 day with lt comparison
        # So date_to=yesterday means < (yesterday + 1 day) which includes yesterday itself
        response = self.client.get(f'/api/sales/?date_to={yesterday.strftime("%Y-%m-%d")}')
        self.assertEqual(response.data['count'], 2)

        # Filter date range: from last_week to yesterday
        # date_to=yesterday with API logic means < (yesterday + 1 day)
        # So it should include last_week and yesterday (2 sales)
        response = self.client.get(
            f'/api/sales/?date_from={last_week.strftime("%Y-%m-%d")}&date_to={yesterday.strftime("%Y-%m-%d")}'
        )
        # API uses lt (yesterday + 1 day) which excludes today but includes yesterday
        # So from last_week to < (yesterday+1) includes last_week, yesterday = 2
        self.assertEqual(response.data['count'], 2)

    def test_update_sale_put_success(self):
        """Test full sale update with PUT"""
        self.authenticate_as_owner()
        sale = Sale.objects.create(
            company=self.company,
            buyer_name='Original Buyer',
            sale_date=timezone.now(),
            total_amount=100.00
        )

        response = self.client.put(f'/api/sales/{sale.id}/', {
            'buyer_name': 'Updated Buyer',
            'sale_date': sale.sale_date.isoformat()
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['buyer_name'], 'Updated Buyer')

    def test_update_sale_patch_success(self):
        """Test partial sale update with PATCH"""
        self.authenticate_as_owner()
        sale = Sale.objects.create(
            company=self.company,
            buyer_name='Original Buyer',
            sale_date=timezone.now(),
            total_amount=100.00
        )

        response = self.client.patch(f'/api/sales/{sale.id}/', {
            'buyer_name': 'Patched Buyer'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['buyer_name'], 'Patched Buyer')

    def test_delete_sale_returns_stock(self):
        """Test deleting sale returns products to stock"""
        self.authenticate_as_owner()
        # Create sale
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Will Be Deleted',
            'product_sales': [
                {'product': self.product.id, 'quantity': 10}
            ]
        }, format='json')
        sale_id = response.data['id']

        # Verify quantity decreased
        self.product.refresh_from_db()
        original_qty = 50
        self.assertEqual(self.product.quantity, original_qty - 10)

        # Delete sale
        response = self.client.delete(f'/api/sales/{sale_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify quantity restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, original_qty)

    def test_delete_sale_not_found(self):
        """Test deleting nonexistent sale"""
        self.authenticate_as_owner()
        response = self.client.delete('/api/sales/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# ACCESS CONTROL TESTS
# =============================================================================

class AccessControlTests(BaseAPITestCase):

    def test_employee_can_read_company(self):
        """Test employee can read company info"""
        self.authenticate_as_employee()
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_can_read_storage(self):
        """Test employee can read storage"""
        self.authenticate_as_employee()
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_can_read_products(self):
        """Test employee can read products"""
        self.authenticate_as_employee()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_can_create_sale(self):
        """Test employee can create sales"""
        self.authenticate_as_employee()
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Employee Sale',
            'product_sales': [
                {'product': self.product.id, 'quantity': 1}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_employee_cannot_update_company(self):
        """Test employee cannot update company - returns 404 because employee has no company via owner path"""
        self.authenticate_as_employee()
        response = self.client.patch('/api/company/update/', {
            'name': 'Unauthorized'
        })
        # UpdateCompanyView checks request.user.company which doesn't exist for employees
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_employee_cannot_delete_company(self):
        """Test employee cannot delete company - returns 404 because employee has no company via owner path"""
        self.authenticate_as_employee()
        response = self.client.delete('/api/company/delete/')
        # DeleteCompanyView checks request.user.company which doesn't exist for employees
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_employee_cannot_update_storage(self):
        """Test employee cannot update storage"""
        self.authenticate_as_employee()
        response = self.client.patch(f'/api/storage/update/{self.storage.id}/', {
            'address': 'Unauthorized'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_delete_storage(self):
        """Test employee cannot delete storage"""
        self.authenticate_as_employee()
        response = self.client.delete(f'/api/storage/delete/{self.storage.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_manage_employees(self):
        """Test employee cannot manage employees - returns 404 because employee has no company via owner path"""
        self.authenticate_as_employee()
        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.new_user.id
        })
        # AttachUserToCompanyView checks request.user.company which doesn't exist for employees
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_access_other_company_products(self):
        """Test user cannot access products from other company"""
        self.authenticate_as_new_user()
        self.client.post('/api/company/create/', {
            'inn': '555566667777',
            'name': 'Other Company'
        })

        # Try to access original company's product
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class IntegrationTests(BaseAPITestCase):

    def test_full_workflow(self):
        """Test complete workflow: register -> create company -> add products -> supply -> sale"""
        # 1. Register new user
        response = self.client.post('/api/register/', {
            'email': 'workflow@example.com',
            'password': 'workflow123',
            'first_name': 'Workflow',
            'last_name': 'Test'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 2. Create company
        response = self.client.post('/api/company/create/', {
            'inn': '777788889999',
            'name': 'Workflow Company'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 3. Create storage
        response = self.client.post('/api/storage/create/', {
            'address': 'Workflow Storage Address'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        storage_id = response.data['id']

        # 4. Create supplier
        response = self.client.post('/api/suppliers/', {
            'name': 'Workflow Supplier',
            'inn': '888899990000',
            'contact_info': 'supplier@workflow.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        supplier_id = response.data['id']

        # 5. Create product
        response = self.client.post('/api/products/', {
            'title': 'Workflow Product',
            'description': 'Product for workflow test',
            'purchase_price': 100.00,
            'sale_price': 150.00
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 0)  # Starts with 0
        product_id = response.data['id']

        # 6. Create supply (add stock)
        response = self.client.post('/api/supplies/create/', [
            {
                'id': product_id,
                'quantity': 100,
                'supplier_id': supplier_id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify product quantity
        response = self.client.get(f'/api/products/{product_id}/')
        self.assertEqual(response.data['quantity'], 100)

        # 7. Create sale
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Workflow Buyer',
            'product_sales': [
                {'product': product_id, 'quantity': 50}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sale_id = response.data['id']
        self.assertEqual(response.data['total_amount'], '7500.00')  # 150 * 50

        # Verify product quantity after sale
        response = self.client.get(f'/api/products/{product_id}/')
        self.assertEqual(response.data['quantity'], 50)  # 100 - 50

        # 8. List sales
        response = self.client.get('/api/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # 9. Get sale details
        response = self.client.get(f'/api/sales/{sale_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['buyer_name'], 'Workflow Buyer')
        self.assertEqual(len(response.data['product_sales']), 1)

    def test_supply_sale_cycle(self):
        """Test supply -> sale -> delete sale -> restock cycle"""
        self.authenticate_as_owner()
        original_qty = self.product.quantity

        # Create supply
        response = self.client.post('/api/supplies/create/', [
            {
                'id': self.product.id,
                'quantity': 20,
                'supplier_id': self.supplier.id
            }
        ], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify quantity increased
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, original_qty + 20)

        # Create sale
        response = self.client.post('/api/sales/create/', {
            'buyer_name': 'Cycle Buyer',
            'product_sales': [
                {'product': self.product.id, 'quantity': 15}
            ]
        }, format='json')
        sale_id = response.data['id']

        # Verify quantity decreased
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, original_qty + 20 - 15)

        # Delete sale
        response = self.client.delete(f'/api/sales/{sale_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify quantity restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, original_qty + 20)

    def test_employee_lifecycle(self):
        """Test employee management: attach -> list -> delete"""
        self.authenticate_as_owner()

        # List employees (should be empty)
        response = self.client.get('/api/company/employees/')
        self.assertEqual(len(response.data), 0)

        # Attach employee
        response = self.client.post('/api/company/attach-user/', {
            'user_id': self.employee.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # List employees (should have 1)
        response = self.client.get('/api/company/employees/')
        self.assertEqual(len(response.data), 1)

        # Delete employee
        response = self.client.delete(f'/api/company/employees/{self.employee.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # List employees (should be empty)
        response = self.client.get('/api/company/employees/')
        self.assertEqual(len(response.data), 0)

    def test_company_crud_lifecycle(self):
        """Test company lifecycle: create -> read -> update -> delete"""
        self.authenticate_as_new_user()

        # Create company
        response = self.client.post('/api/company/create/', {
            'inn': '999900001111',
            'name': 'Lifecycle Company'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        company_id = response.data['id']

        # Read company
        response = self.client.get('/api/company/')
        self.assertEqual(response.data['name'], 'Lifecycle Company')

        # Update company (PATCH)
        response = self.client.patch('/api/company/update/', {
            'name': 'Updated Lifecycle Company'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Lifecycle Company')

        # Delete company
        response = self.client.delete('/api/company/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Try to read (should fail)
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
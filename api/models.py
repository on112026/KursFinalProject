from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_company_owner = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def get_companies(self):
        """
        Возвращает QuerySet компаний, к которым имеет доступ пользователь:
        - Компании, где он владелец (owner)
        - Компании, где он в списке участников (users)
        """
        owner_companies = Company.objects.filter(owner=self)
        member_companies = Company.objects.filter(users=self)
        return owner_companies | member_companies

    def can_access_company(self, company):
        """Проверяет, имеет ли пользователь доступ к компании"""
        return company.owner == self or company.users.filter(pk=self.pk).exists()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]

class Company(models.Model):
    inn = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    users = models.ManyToManyField(User, related_name='company_users', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Storage(models.Model):
    address = models.TextField()
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='storage')

    def __str__(self):
        return f"Storage for {self.company.name}"

class Supplier(models.Model):
    """Модель поставщика"""
    name = models.CharField(max_length=255)
    inn = models.CharField(max_length=12, blank=True, default='')
    contact_info = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Product(models.Model):
    """Модель товара"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class Supply(models.Model):
    """Модель поставки товаров"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplies')
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, related_name='supplies')
    delivery_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Supply #{self.id} from {self.supplier.name}"

    class Meta:
        ordering = ['-delivery_date']

class SupplyProduct(models.Model):
    """Промежуточная модель для связи Supply и Product"""
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='supply_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supply_products')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.title} x{self.quantity} in Supply #{self.supply.id}"


class Sale(models.Model):
    """Модель продажи"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales')
    buyer_name = models.CharField(max_length=255)
    sale_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale #{self.id} - {self.buyer_name}"

    class Meta:
        ordering = ['-sale_date']


class ProductSale(models.Model):
    """Промежуточная модель для связи Sale и Product"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='product_sales')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_sales')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x{self.quantity} in Sale #{self.sale.id}"

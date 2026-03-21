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
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]

class Company(models.Model):
    inn = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')

    def __str__(self):
        return self.name

class Storage(models.Model):
    address = models.TextField()
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='storage')

    def __str__(self):
        return f"Storage for {self.company.name}"
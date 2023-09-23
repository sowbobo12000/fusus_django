from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, organization_id=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        # Fetch the Organization instance by its ID
        organization = None
        if organization_id:
            organization = Organization.objects.get(pk=organization_id)

        user = self.model(email=email, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, organization_id=None, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if 'organization' in extra_fields:
            del extra_fields['organization']
        return self.create_user(email, organization_id, password, **extra_fields)


class Organization(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    address = models.TextField()


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('VIEWER', 'Viewer'),
        ('USER', 'User'),
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    birthdate = models.DateField()
    is_staff = models.BooleanField(default=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='USER')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'organization_id', 'birthdate']

    objects = UserManager()

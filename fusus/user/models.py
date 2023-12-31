from django.db import models
from org.models import Organization
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, email, organization_id=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        organization = None
        if organization_id:
            organization = Organization.objects.get(pk=organization_id)

        user = self.model(email=email, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        group_map = {
            'ADMIN': 'Administrator',
            'VIEWER': 'Viewer',
            'USER': 'User'
        }

        group_name = group_map.get(extra_fields.get('user_type'))
        if group_name:
            try:
                user_group = Group.objects.get(name=group_name)
                user.groups.add(user_group)
            except Group.DoesNotExist:
                pass

        return user

    def create_superuser(self, email, organization_id=None, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, organization_id, password, **extra_fields)


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

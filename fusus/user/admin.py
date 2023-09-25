from django.contrib import admin
from .models import  User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'user_type', 'organization', 'is_staff')
    search_fields = ('name', 'email',)
    list_filter = ('user_type', 'is_staff')

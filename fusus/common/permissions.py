from rest_framework.permissions import BasePermission
from enum import Enum


class UserType(Enum):
    ADMINISTRATOR = "ADMIN"
    VIEWER = "VIEWER"
    USER = "USER"


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == UserType.ADMINISTRATOR.value


class IsViewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == UserType.VIEWER.value


class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == UserType.USER.value

    def has_object_permission(self, request, view, obj):
        return obj == request.user

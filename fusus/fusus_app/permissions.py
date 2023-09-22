from rest_framework import permissions


class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'Administrator'


class IsViewerOrAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type in ['Viewer', 'Administrator']

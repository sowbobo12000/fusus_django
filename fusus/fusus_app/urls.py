from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, OrganizationViewSet, login, GroupView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'organizations', OrganizationViewSet)

urlpatterns = [
    path('auth/login/', login, name='user-login'),
    path('auth/groups/', GroupView.as_view(), name='user-groups'),
    path('', include(router.urls)),
]
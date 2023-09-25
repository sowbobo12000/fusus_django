from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoginView, GroupView, InfoView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/groups/', GroupView.as_view(), name='auth-groups'),
    path('info/', InfoView.as_view(), name='info'),
    path('', include(router.urls)),
]

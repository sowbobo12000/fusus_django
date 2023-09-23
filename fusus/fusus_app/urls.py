from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, login, GroupView, OrganizationDetailView, OrganizationUsersListView, \
    OrganizationUserDetailView, InfoView, user_create, user_list

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('auth/login/', login, name='user-login'),
    path('auth/groups/', GroupView.as_view(), name='user-groups'),
    path('users/create/', user_create, name='user_create'),
    path('users/', user_list, name='user_list'),
    path('info/', InfoView.as_view(), name='info'),
    re_path(r'^organizations/(?P<pk>\d+)/$', OrganizationDetailView.as_view(), name='organization-detail'),
    re_path(r'^organizations/(?P<pk>\d+)/users/$', OrganizationUsersListView.as_view(), name='organization-users-list'),
    re_path(r'^organizations/(?P<org_id>\d+)/users/(?P<user_id>\d+)/$', OrganizationUserDetailView.as_view(),
            name='organization-user-detail'),
    path('', include(router.urls)),
]

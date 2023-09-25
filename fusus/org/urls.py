from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import OrganizationDetailView, OrganizationUsersListView, OrganizationUserDetailView

router = DefaultRouter()

urlpatterns = [
    re_path(r'^organizations/(?P<pk>\d+)/$', OrganizationDetailView.as_view(), name='organization-detail'),
    re_path(r'^organization/(?P<pk>\d+)/users/$', OrganizationUsersListView.as_view(), name='organization-users-list'),
    re_path(r'^organization/(?P<org_id>\d+)/users/(?P<user_id>\d+)/$', OrganizationUserDetailView.as_view(),
            name='organization-user-detail'),
    path('', include(router.urls)),
]

from rest_framework import serializers, viewsets
from rest_framework_jwt.views import obtain_jwt_token
from django.contrib.auth.models import Group
from .models import User, Organization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class GroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']

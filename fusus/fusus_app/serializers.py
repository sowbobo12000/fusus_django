from rest_framework import serializers, viewsets
from .models import User, Organization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name']


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class GroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']

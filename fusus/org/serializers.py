from rest_framework import serializers, viewsets
from .models import Organization
from user.models import User


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    address = serializers.CharField(required=False)

    class Meta:
        model = Organization
        fields = '__all__'


class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name']

from django.shortcuts import render
from rest_framework import serializers, viewsets
from .serializers import UserSerializer, GroupsSerializer
from .models import User, Organization
from rest_framework_jwt.settings import api_settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from enum import Enum


class UserType(Enum):
    ADMINISTRATOR = "Administrator"
    VIEWER = "Viewer"
    USER = "User"


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


@api_view(['POST'])
def login(request):
    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return Response({'token': token})
    except User.DoesNotExist:
        return Response({'error': 'Invalid Email'}, status=400)


class GroupView(APIView):

    def get(self, request):
        admins = User.objects.filter(user_type=UserType.ADMINISTRATOR.value)
        viewers = User.objects.filter(user_type=UserType.VIEWER.value)
        users = User.objects.filter(user_type=UserType.USER.value)

        admin_data = GroupsSerializer(admins, many=True).data
        viewer_data = GroupsSerializer(viewers, many=True).data
        user_data = GroupsSerializer(users, many=True).data

        data = {
            "Administrators": admin_data,
            "Viewers": viewer_data,
            "Users": user_data
        }

        return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
    search_fields = ['name', 'email']
    filter_fields = ['phone']

    def get_queryset(self):
        token = self.request.headers.get('Authorization').split()[1]
        payload = api_settings.JWT_DECODE_HANDLER(token)
        user_type = payload.get("user_type")

        if user_type in ['VIEWER', 'ADMINISTRATOR']:
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            return self.queryset.filter(organization=user.organization)

        return self.queryset.none()

    def create(self, request):
        token = request.headers.get('Authorization').split()[1]
        payload = api_settings.JWT_DECODE_HANDLER(token)
        user_type = payload.get("user_type")

        if user_type == UserType.VIEWER.value:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        elif user_type == UserType.ADMINISTRATOR.value:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif user_type == UserType.USER.value:
            return


    def update(self, request, pk=None):
        token = request.headers.get('Authorization').split()[1]
        payload = api_settings.JWT_DECODE_HANDLER(token)
        user_type = payload.get("user_type")
        user_id = payload.get("user_id")

        user = self.get_object()

        if user_type == "ADMINISTRATOR" or int(user_id) == user.id:
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        token = request.headers.get('Authorization').split()[1]
        payload = api_settings.JWT_DECODE_HANDLER(token)
        user_type = payload.get("user_type")

        if user_type != "ADMINISTRATOR":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


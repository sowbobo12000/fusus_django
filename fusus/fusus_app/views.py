from rest_framework import serializers, viewsets
from .serializers import UserSerializer, OrganizationSerializer, GroupsSerializer, MinimalUserSerializer
from .models import User, Organization
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
import requests
from django.shortcuts import render, redirect

from enum import Enum


class UserTypeMixin:
    def get_payload_from_token(self):
        token = self.request.headers.get('Authorization').split()[1]
        decoded_token = RefreshToken(token)
        return decoded_token.payload


class UserType(Enum):
    ADMINISTRATOR = "Administrator"
    VIEWER = "Viewer"
    USER = "User"


@api_view(['POST'])
def login(request):
    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
    except User.DoesNotExist:
        return Response({'error': 'Invalid Email'}, status=400)

def user_create(request):
    if request.method == "POST":
        # 폼에서 제공된 데이터로 사용자 생성 로직 추가
        name = request.POST['name']
        phone = request.POST['phone']
        email = request.POST['email']
        organization = Organization.objects.get(id=request.POST['organization'])
        birthdate = request.POST['birthdate']
        user_type = request.POST['user_type']
        password = request.POST['password']

        user = User(
            name=name,
            phone=phone,
            email=email,
            organization=organization,
            birthdate=birthdate,
            user_type=user_type
        )
        user.set_password(password)
        user.save()

        return redirect('user_list')  # 사용자 목록 페이지로 리디렉션
    else:
        organizations = Organization.objects.all()
        return render(request, 'create_user.html', {'organizations': organizations})
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})


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


class UserViewSet(viewsets.ModelViewSet, UserTypeMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    search_fields = ['name', 'email']
    filter_fields = ['phone']

    def get_queryset(self):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type in [UserType.ADMINISTRATOR.value, UserType.VIEWER.value]:
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            return self.queryset.filter(organization=user.organization)

        return self.queryset.none()

    def create(self, request):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return Response({"detail": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if user_type == UserType.USER.value:
            if email != payload.get("email"):
                return Response({"detail": "Not authorized to create account for others"},
                                status=status.HTTP_403_FORBIDDEN)

        if user_type == UserType.VIEWER.value:
            return Response({"detail": "Not authorized for Viewer"}, status=status.HTTP_403_FORBIDDEN)

        if user_type in [UserType.ADMINISTRATOR.value, UserType.USER.value]:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        payload = self.get_payload_from_token()
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
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type != "ADMINISTRATOR":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationDetailView(APIView, UserTypeMixin):

    def get_object(self, pk):
        try:
            return Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            raise status.Http404

    def get(self, request, pk):
        organization = self.get_object(pk)
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type not in [UserType.ADMINISTRATOR.value, UserType.VIEWER.value]:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)

    def patch(self, request, pk):
        organization = self.get_object(pk)
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type != UserType.ADMINISTRATOR.value:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationUsersListView(APIView, UserTypeMixin):

    def get(self, request, pk):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type not in [UserType.ADMINISTRATOR.value, UserType.VIEWER.value]:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.filter(organization_id=pk)
        serializer = MinimalUserSerializer(users, many=True)
        return Response(serializer.data)


class OrganizationUserDetailView(APIView, UserTypeMixin):

    def get(self, request, org_id, user_id):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type not in [UserType.ADMINISTRATOR.value, UserType.VIEWER.value]:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, organization_id=org_id, id=user_id)
        serializer = MinimalUserSerializer(user)
        return Response(serializer.data)


class InfoView(APIView):
    def get(self, request):
        try:
            user = request.user

            public_ip = requests.get('https://api.ipify.org').text

            data = {
                'user_name': user.username,
                'id': user.id,
                'organization_name': user.organization.name,
                'public_ip': public_ip
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

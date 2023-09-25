import requests
from .serializers import UserSerializer, OrganizationSerializer, GroupsSerializer, MinimalUserSerializer
from .models import User, Organization
from rest_framework import filters, status, serializers, viewsets
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from enum import Enum


class UserTypeMixin:
    def get_payload_from_token(self):
        token = self.request.headers.get('Authorization').split()[1]
        decoded_token = AccessToken(token)
        user_id = decoded_token["user_id"]

        user = User.objects.get(id=user_id)

        payload = {
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'organization': user.organization.name if user.organization else None,
            'birthdate': user.birthdate,
            'user_type': user.user_type
        }

        return payload


class UserType(Enum):
    ADMINISTRATOR = "ADMIN"
    VIEWER = "VIEWER"
    USER = "USER"


@api_view(['POST'])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(email=email, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
    else:
        return Response({'error': 'Invalid Email or Password'}, status=400)


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
    queryset = User.objects.all().select_related('organization')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    search_fields = ['name', 'email']
    filter_fields = ['phone']

    def get_queryset(self):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")
        user_id = payload.get("user_id")

        if user_type == UserType.ADMINISTRATOR.value or user_type == UserType.VIEWER.value:
            user = User.objects.get(id=user_id)
            return self.queryset.filter(organization=user.organization)

        elif user_type == UserType.USER.value:
            return self.queryset.filter(id=user_id)

        return self.queryset.none()

    def retrieve(self, request, *args, **kwargs):
        payload = self.get_payload_from_token()
        user_id = payload.get("user_id")
        requesting_user = User.objects.get(id=user_id)

        user_from_db = User.objects.filter(id=kwargs.get('pk')).first()
        if not user_from_db or user_from_db.organization != requesting_user.organization:
            return Response({"detail": "Not authorized to view user from another organization"},
                            status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()

        serializer = self.get_serializer(user)
        return Response(serializer.data)

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

            name = request.data.get("name")
            phone = request.data.get("phone")
            birthdate = request.data.get("birthdate")
            organization_id = request.data.get("organization")
            user_type = request.data.get("user_type")
            password = request.data.get("password")

            try:
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    phone=phone,
                    birthdate=birthdate,
                    organization_id=organization_id,
                    user_type=user_type,
                    password=password
                )
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"detail": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, partial=False):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")
        user_id = payload.get("user_id")

        user = self.get_object()

        if user_type == UserType.ADMINISTRATOR.value or int(user_id) == user.id:

            if "password" in request.data:
                user.set_password(request.data["password"])
                user.save()

                updated_data = request.data.copy()
                del updated_data["password"]
            else:
                updated_data = request.data

            serializer = UserSerializer(user, data=updated_data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type != UserType.ADMINISTRATOR.value:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


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

    def patch(self, request, pk, partial=False):
        organization = self.get_object(pk)
        payload = self.get_payload_from_token()
        user_type = payload.get("user_type")

        if user_type != UserType.ADMINISTRATOR.value:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganizationSerializer(organization, data=request.data, partial=partial)
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
                'user_name': user.name,
                'id': user.id,
                'organization_name': user.organization.name,
                'public_ip': public_ip
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

import requests
from .serializers import UserSerializer, GroupSerializer
from .models import User
from rest_framework import filters, status, serializers, viewsets
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from enum import Enum
from django.contrib.auth.models import Group
from common.permissions import IsAdministrator, IsViewer, IsUser


class UserType(Enum):
    ADMINISTRATOR = "ADMIN"
    VIEWER = "VIEWER"
    USER = "USER"


class LoginView(APIView):
    def post(self, request):
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
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('organization')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    search_fields = ['name', 'email']
    filter_fields = ['phone']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdministrator]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAdministrator | IsUser]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [IsAdministrator | IsViewer | IsUser]
        else:
            permission_classes = [IsAdministrator]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == UserType.ADMINISTRATOR.value or user.user_type == UserType.VIEWER.value:
            return self.queryset.filter(organization=user.organization)
        elif user.user_type == UserType.USER.value:
            return self.queryset.filter(id=user.id)

        return self.queryset.none()

    def retrieve(self, request, *args, **kwargs):
        requesting_user = request.user
        user_from_db = User.objects.filter(id=kwargs.get('pk')).first()

        if not user_from_db or user_from_db.organization != requesting_user.organization:
            return Response({"detail": "Not authorized to view user from another organization"},
                            status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def create(self, request):
        user_type = request.user.user_type
        email = request.data.get("email")

        if User.objects.filter(email=email).exists():
            return Response({"detail": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if user_type == UserType.USER.value and email != request.user.email:
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
        user_type = request.user.user_type
        user = self.get_object()

        if (user_type == UserType.ADMINISTRATOR.value and
                request.user.organization == user.organization) or IsUser().has_object_permission(request, None, user):
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
        user_type = request.user.user_type

        if user_type != UserType.ADMINISTRATOR.value:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class InfoView(APIView):
    permission_classes = [IsAdministrator | IsViewer | IsUser]

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

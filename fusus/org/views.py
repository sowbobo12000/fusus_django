from .serializers import OrganizationSerializer, MinimalUserSerializer
from .models import Organization
from user.models import User
from rest_framework import filters, status, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from common.permissions import IsAdministrator, IsViewer


class OrganizationDetailView(APIView):
    permission_classes = [IsAdministrator | IsViewer]

    def get_object(self, pk):
        try:
            return Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            raise status.Http404

    def get(self, request, pk):
        organization = self.get_object(pk)
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)

    def patch(self, request, pk, partial=False):
        organization = self.get_object(pk)
        serializer = OrganizationSerializer(organization, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationUsersListView(APIView):
    permission_classes = [IsAdministrator | IsViewer]

    def get(self, request, pk):
        users = User.objects.filter(organization_id=pk)
        serializer = MinimalUserSerializer(users, many=True)
        return Response(serializer.data)


class OrganizationUserDetailView(APIView):
    permission_classes = [IsAdministrator | IsViewer]

    def get(self, request, org_id, user_id):
        user = get_object_or_404(User, organization_id=org_id, id=user_id)
        serializer = MinimalUserSerializer(user)
        return Response(serializer.data)

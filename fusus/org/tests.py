from django.urls import reverse
from rest_framework import status
from user.models import User
from common.tests.base import BaseTestCase


class OrganizationTests(BaseTestCase):

    def test_retrieve_organization_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        url = reverse('organization-detail', args=[self.org1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.org1.id)

    def test_retrieve_organization_viewer(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        url = reverse('organization-detail', args=[self.org1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.org1.id)

    def test_update_organization_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        url = reverse('organization-detail', args=[self.org1.id])
        updated_data = {"name": "Updated Org Name"}
        response = self.client.patch(url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Org Name")

    def test_update_organization_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["USER"]["TestOrg1"][0])
        url = reverse('organization-detail', args=[self.org1.id])
        updated_data = {"name": "Try Updating"}
        response = self.client.patch(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_for_organization_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        url = reverse('organization-users-list', args=[self.org1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user_data in response.data:
            self.assertCountEqual(user_data.keys(), ["id", "name"])

    def test_list_users_for_organization_viewer(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        url = reverse('organization-users-list', args=[self.org1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user_data in response.data:
            self.assertCountEqual(user_data.keys(), ["id", "name"])

    def test_retrieve_user_for_organization_admin(self):
        user = User.objects.filter(organization=self.org1).first()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        url = reverse('organization-user-detail', args=[self.org1.id, user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ["id", "name"])

    def test_retrieve_user_for_organization_viewer(self):
        user = User.objects.filter(organization=self.org1).first()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        url = reverse('organization-user-detail', args=[self.org1.id, user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ["id", "name"])

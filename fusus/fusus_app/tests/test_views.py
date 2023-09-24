from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from fusus_app.models import User, Organization
from rest_framework_simplejwt.tokens import RefreshToken


class BaseTestCase(APITestCase):

    def setUp(self):
        self.org1 = Organization.objects.create(name="TestOrg1")
        self.org2 = Organization.objects.create(name="TestOrg2")

        self.tokens = {}
        user_types = ["ADMIN", "VIEWER", "USER"]

        for user_type in user_types:
            self.tokens[user_type] = {}
            for idx, org in enumerate([self.org1, self.org2], 1):
                users = []
                if user_type == "ADMIN":
                    user = User.objects.create_superuser(
                        email=f"{user_type.lower()}{idx}@testorg{idx}.com",
                        password="password",
                        name=f"{user_type} User {idx}",
                        organization_id=org.id,
                        birthdate='1992-12-20'
                    )
                    users.append(user)
                else:
                    for i in range(1, 5):
                        user = User.objects.create_user(
                            email=f"{user_type.lower()}{i}@testorg{idx}.com",
                            password="password",
                            name=f"{user_type} User {i}",
                            user_type=user_type,
                            organization_id=org.id,
                            birthdate='1992-12-20'
                        )
                        users.append(user)

                self.tokens[user_type][org.name] = [
                    str(RefreshToken.for_user(user).access_token) for user in users
                ]


class AuthTests(BaseTestCase):

    def test_login(self):
        url = reverse('user-login')
        data = {"email": "admin1@testorg1.com", "password": "password"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_auth_groups(self):
        url = reverse('user-groups')
        # Using Admin Token for org1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Administrators", response.data)
        self.assertIn("Viewers", response.data)
        self.assertIn("Users", response.data)


class UserTests(BaseTestCase):

    def test_list_users_admin(self):
        url = reverse('users-list')
        # Admin token for org1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 3)

    def test_create_user_admin(self):
        url = reverse('users-list')
        data = {
            "email": "newuser@test.com",
            "name": "New User",
            "password": "password",
            # Add other necessary fields
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OrganizationTests(BaseTestCase):

    def test_retrieve_organization_admin(self):
        url = reverse('organization-detail', kwargs={"pk": self.org1.pk})
        # Admin token for org1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "TestOrg1")


class OtherTests(BaseTestCase):

    def test_info(self):
        url = reverse('info')
        # Admin token for org1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user_name", response.data)
        self.assertIn("public_ip", response.data)

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from fusus_app.models import User, Organization
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.db.models import Q


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

        for user_type, orgs in self.tokens.items():
            for org_name, tokens in orgs.items():
                if user_type == "ADMIN":
                    for idx, token in enumerate(tokens, start=1):
                        email = f"{user_type.lower()}{idx}@testorg{idx}.com"
                        data = {"email": email, "password": "password"}
                        response = self.client.post(url, data, format='json')
                        self.assertEqual(response.status_code, status.HTTP_200_OK)
                        self.assertIn("access", response.data)
                else:
                    for i in range(1, 5):
                        email = f"{user_type.lower()}{i}@testorg{idx}.com"
                        data = {"email": email, "password": "password"}
                        response = self.client.post(url, data, format='json')
                        self.assertEqual(response.status_code, status.HTTP_200_OK)
                        self.assertIn("access", response.data)

    def test_auth_groups(self):
        url = reverse('user-groups')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_admin_count = 2
        expected_viewer_count = 8
        expected_user_count = 8

        self.assertEqual(len(response.data["Administrators"]), expected_admin_count)
        self.assertEqual(len(response.data["Viewers"]), expected_viewer_count)
        self.assertEqual(len(response.data["Users"]), expected_user_count)


class UserTests(BaseTestCase):

    def test_list_users_as_admin(self):
        url = reverse('users-list')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg2"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

    def test_create_user_admin(self):
        url = reverse('users-list')
        data = {
            "email": "newuser@test.com",
            "name": "New User",
            "password": "password",
            "phone": "919",
            "birthdate": "1992-12-20",
            "user_type": "USER",
            "organization": self.org2.id
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_as_viewer(self):
        url = reverse('users-list')
        data = {
            "email": "newuser2@test.com",
            "name": "New User 2",
            "password": "password2",
            "phone": "920",
            "birthdate": "1993-12-21",
            "user_type": "USER",
            "organization": self.org2.id
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Not authorized for Viewer")

    def test_create_user_as_user(self):
        url = reverse('users-list')
        data = {
            "email": "differentuser@test.com",
            "name": "Different User",
            "password": "password3",
            "phone": "921",
            "birthdate": "1994-12-22",
            "user_type": "USER",
            "organization": self.org2.id
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["USER"]["TestOrg1"][0])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Not authorized to create account for others")

    def test_retrieve_user_as_admin(self):
        user_to_retrieve = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', kwargs={'pk': user_to_retrieve.id})

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user_to_retrieve.id)
        self.assertIn('organization', response.data)

    def test_retrieve_user_as_viewer(self):
        user_to_retrieve = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', kwargs={'pk': user_to_retrieve.id})

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user_to_retrieve.id)
        self.assertIn('organization', response.data)

    def test_retrieve_user_as_user(self):
        user = User.objects.filter(user_type='USER', organization=self.org1).first()
        url = reverse('users-detail', kwargs={'pk': user.id})

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["USER"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user.id)
        self.assertIn('organization', response.data)

        another_user = User.objects.filter(~Q(id=user.id), organization=self.org1).first()
        url = reverse('users-detail', kwargs={'pk': another_user.id})
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_users_admin_wrong_org(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg2"][0])
        user_from_org1 = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', args=[user_from_org1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_users_viewer_wrong_org(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg2"][0])

        user_from_org1 = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', args=[user_from_org1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_admin_same_org(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        user_from_org1 = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', args=[user_from_org1.id])
        updated_data = {"name": "Updated Name"}
        response = self.client.patch(url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")

    def test_update_user_self(self):
        user_from_org1 = User.objects.filter(organization=self.org1, user_type='USER').first()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["USER"]["TestOrg1"][0])
        url = reverse('users-detail', args=[user_from_org1.id])
        updated_data = {"name": "Updated Self Name"}
        response = self.client.patch(url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Self Name")

    def test_delete_user_admin_same_org(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        user_from_org1 = User.objects.filter(organization=self.org1).first()
        url = reverse('users-detail', args=[user_from_org1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_from_org1.id).exists())


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


class OtherTests(BaseTestCase):

    def test_info(self):
        url = reverse('info')

        user_token = self.tokens["ADMIN"]["TestOrg1"][0]
        decoded_token = AccessToken(user_token)
        user = User.objects.get(id=decoded_token["user_id"])
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + user_token)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["user_name"], user.name)
        self.assertEqual(response.data["id"], user.id)
        self.assertEqual(response.data["organization_name"], user.organization.name)

        self.assertIn("public_ip", response.data)

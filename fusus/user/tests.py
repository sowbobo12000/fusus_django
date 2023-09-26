from django.urls import reverse
from rest_framework import status
from user.models import User, Organization
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.db.models import Q
from common.tests.base import BaseTestCase


class AuthTests(BaseTestCase):

    def test_login(self):
        url = reverse('auth-login')

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
        url = reverse('auth-groups')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        group_names = [group['name'] for group in response.data]

        self.assertIn("Administrator", group_names)
        self.assertIn("Viewer", group_names)
        self.assertIn("User", group_names)


class UserTests(BaseTestCase):

    def test_list_users_as_admin(self):
        url = reverse('users-list')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg2"][0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_users_by_name_as_admin(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        search_name = "ADMIN User 1"
        response = self.client.get(url, {'search': search_name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], search_name)

    def test_search_users_by_email_as_admin(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        search_email = "admin1@testorg1.com"
        response = self.client.get(url, {'search': search_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['email'], search_email)

    def test_search_users_by_name_as_viewer(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        search_name = "ADMIN User 1"
        response = self.client.get(url, {'search': search_name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], search_name)

    def test_search_users_by_email_as_viewer(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        search_email = "admin1@testorg1.com"
        response = self.client.get(url, {'search': search_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['email'], search_email)

    def test_filter_users_by_phone_as_admin(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["ADMIN"]["TestOrg1"][0])
        filter_phone = "1000000001"
        response = self.client.get(url, {'phone': filter_phone})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['phone'], filter_phone)

    def test_filter_users_by_phone_as_viewer(self):
        url = reverse('users-list')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.tokens["VIEWER"]["TestOrg1"][0])
        filter_phone = "1000000001"
        response = self.client.get(url, {'phone': filter_phone})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['phone'], filter_phone)

    def test_create_user_admin(self):
        url = reverse('users-list')
        data = {
            "email": "newuser@test.com",
            "name": "New User",
            "password": "password",
            "phone": "919",
            "birthdate": "1992-12-20",
            "user_type": "USER",
            "organization": self.org1.id
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

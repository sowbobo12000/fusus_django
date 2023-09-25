from rest_framework.test import APITestCase
from org.models import Organization
from user.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class BaseTestCase(APITestCase):

    def setUp(self):
        self.org1 = Organization.objects.create(name="TestOrg1")
        self.org2 = Organization.objects.create(name="TestOrg2")

        self.tokens = {}
        user_types = ["ADMIN", "VIEWER", "USER"]
        phone_counter = 1

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
                        phone=str(1000000000 + phone_counter),
                        birthdate='1992-12-20'
                    )
                    phone_counter += 1
                    users.append(user)
                else:
                    for i in range(1, 5):
                        user = User.objects.create_user(
                            email=f"{user_type.lower()}{i}@testorg{idx}.com",
                            password="password",
                            name=f"{user_type} User {i}",
                            user_type=user_type,
                            organization_id=org.id,
                            phone=str(1000000000 + phone_counter),
                            birthdate='1992-12-20'
                        )
                        phone_counter += 1
                        users.append(user)

                self.tokens[user_type][org.name] = [
                    str(RefreshToken.for_user(user).access_token) for user in users
                ]
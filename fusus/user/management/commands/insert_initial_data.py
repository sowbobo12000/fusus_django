from django.core.management.base import BaseCommand
from user.models import User
from org.models import Organization


class Command(BaseCommand):
    help = 'Inserts initial data into the database'

    def handle(self, *args, **kwargs):
        org1 = Organization.objects.create(name='Organization1', phone='123456789', address='Address1')
        org2 = Organization.objects.create(name='Organization2', phone='987654321', address='Address2')

        for user_type in ['ADMIN', 'VIEWER', 'USER']:
            for idx, org in enumerate([org1, org2], 1):
                # Create 2 users
                for i in range(1, 3):
                    User.objects.create_user(
                        email=f'{user_type.lower()}{(idx - 1) * 2 + i}@example.com',
                        name=f'{user_type} User {(idx - 1) * 2 + i}',
                        organization_id=org.id,
                        birthdate='1990-01-01',
                        user_type=user_type,
                        password='123123'
                    )

        self.stdout.write(self.style.SUCCESS('Successfully inserted initial data'))

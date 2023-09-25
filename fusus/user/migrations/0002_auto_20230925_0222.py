from django.db import migrations, models


def create_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    administrator_group, _ = Group.objects.get_or_create(name='Administrator')
    viewer_group, _ = Group.objects.get_or_create(name='Viewer')
    user_group, _ = Group.objects.get_or_create(name='User')

    permissions = Permission.objects.filter(content_type__app_label='user', content_type__model='user')
    for permission in permissions:
        administrator_group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions)
    ]

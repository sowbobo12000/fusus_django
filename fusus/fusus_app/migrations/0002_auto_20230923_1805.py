from django.db import migrations

def insert_initial_data(apps, schema_editor):
    Organization = apps.get_model('fusus_app', 'Organization')
    Organization.objects.create(name='Organization1', phone='123456789', address='Address1')
    Organization.objects.create(name='Organization2', phone='987654321', address='Address2')

class Migration(migrations.Migration):

    dependencies = [
        ('fusus_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_initial_data),
    ]

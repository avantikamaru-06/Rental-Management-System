from django.db import migrations


def create_existing_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for user in User.objects.all().iterator():
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'admin' if (user.is_staff or user.is_superuser) else 'customer'},
        )


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_userprofile')]
    operations = [migrations.RunPython(create_existing_profiles, migrations.RunPython.noop)]

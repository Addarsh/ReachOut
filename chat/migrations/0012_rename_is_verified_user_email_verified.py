# Generated by Django 4.1.1 on 2022-10-21 04:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_user_is_verified'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='is_verified',
            new_name='email_verified',
        ),
    ]

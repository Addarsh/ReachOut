# Generated by Django 4.1.1 on 2022-10-09 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_alter_user_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroomuser',
            name='last_read_time',
            field=models.DateTimeField(null=True),
        ),
    ]

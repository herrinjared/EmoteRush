# Generated by Django 5.2 on 2025-04-06 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('users', '0004_user_is_artist_user_is_developer_user_is_founder'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['date_created'], name='idx_date_created'),
        ),
    ]

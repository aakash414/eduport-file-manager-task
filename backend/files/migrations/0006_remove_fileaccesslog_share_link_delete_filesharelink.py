# Generated by Django 4.2 on 2025-07-05 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0005_fileupload_duplicate_of'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileaccesslog',
            name='share_link',
        ),
        migrations.DeleteModel(
            name='FileShareLink',
        ),
    ]

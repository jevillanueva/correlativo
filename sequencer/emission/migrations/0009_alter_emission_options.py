# Generated by Django 5.0.6 on 2024-06-15 18:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emission', '0008_globalsettings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emission',
            options={'permissions': [('can_administrate', 'Can Administrate emission')]},
        ),
    ]

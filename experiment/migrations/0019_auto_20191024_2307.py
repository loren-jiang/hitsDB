# Generated by Django 2.2.2 on 2019-10-24 23:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0018_soak_visitcount'),
    ]

    operations = [
        migrations.RenameField(
            model_name='soak',
            old_name='visitCount',
            new_name='saveCount',
        ),
    ]
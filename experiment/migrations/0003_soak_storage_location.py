# Generated by Django 2.2.6 on 2019-12-11 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0002_auto_20191206_0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='soak',
            name='storage_location',
            field=models.CharField(default='', max_length=20),
        ),
    ]

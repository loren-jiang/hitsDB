# Generated by Django 2.2.2 on 2019-10-24 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0015_auto_20191024_2025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plate',
            name='name',
            field=models.CharField(max_length=20),
        ),
    ]

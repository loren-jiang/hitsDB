# Generated by Django 2.2.2 on 2019-10-24 19:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0010_auto_20191024_1938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='well',
            name='name',
            field=models.CharField(max_length=3, validators=[django.core.validators.RegexValidator(inverse_match=True, message='Enter valid well name', regex='^[A-Z]\\d{2}$')]),
        ),
    ]
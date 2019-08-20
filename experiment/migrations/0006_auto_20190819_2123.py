# Generated by Django 2.2.2 on 2019-08-19 21:23

import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import experiment.models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0005_auto_20190819_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='subwell_locations',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(3), django.core.validators.MinValueValidator(1)]), default=experiment.models.defaultSubwellLocations, size=3),
        ),
    ]

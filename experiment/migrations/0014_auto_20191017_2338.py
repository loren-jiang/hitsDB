# Generated by Django 2.2.2 on 2019-10-17 23:38

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0013_experiment_platedata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='plateData',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]

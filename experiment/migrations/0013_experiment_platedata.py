# Generated by Django 2.2.2 on 2019-10-17 23:37

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0012_auto_20191017_2305'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='plateData',
            field=django.contrib.postgres.fields.jsonb.JSONField(default='{}'),
        ),
    ]

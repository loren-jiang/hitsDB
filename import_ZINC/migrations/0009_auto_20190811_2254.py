# Generated by Django 2.2.2 on 2019-08-12 05:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('import_ZINC', '0008_auto_20190708_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='library',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='group_libraries', to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='library',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='libraries', to=settings.AUTH_USER_MODEL),
        ),
    ]

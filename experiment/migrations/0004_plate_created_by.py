# Generated by Django 2.2.6 on 2019-12-11 23:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiment', '0003_soak_storage_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='plate',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plates_create', to=settings.AUTH_USER_MODEL),
        ),
    ]

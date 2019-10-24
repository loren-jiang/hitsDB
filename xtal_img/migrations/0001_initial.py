# Generated by Django 2.2.2 on 2019-10-23 20:23

from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import s3.s3utils
import uuid
import xtal_img.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('experiment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DropImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('upload', models.ImageField(storage=s3.s3utils.PrivateMediaStorage(), upload_to=xtal_img.models.well_image_upload_path)),
                ('file_name', models.CharField(max_length=10)),
                ('useS3', models.BooleanField(default=True)),
                ('local_upload', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=xtal_img.models.upload_local_path)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drop_images', to=settings.AUTH_USER_MODEL)),
                ('plate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drop_images', to='experiment.Plate')),
            ],
        ),
    ]

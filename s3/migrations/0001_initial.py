# Generated by Django 2.2.2 on 2019-10-18 20:43

from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import s3.models
import s3.s3utils
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiment', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('upload', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='WellImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('upload', models.ImageField(blank=True, null=True, storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.upload_path)),
                ('file_name', models.CharField(max_length=10)),
                ('useS3', models.BooleanField(default=True)),
                ('local_upload', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.upload_local_path)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='well_images', to=settings.AUTH_USER_MODEL)),
                ('plate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='well_images', to='experiment.Plate')),
            ],
            options={
                'ordering': ('file_name',),
            },
        ),
        migrations.CreateModel(
            name='PrivateFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('upload', models.FileField(storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.upload_path)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

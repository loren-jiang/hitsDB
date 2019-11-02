# Generated by Django 2.2.6 on 2019-11-01 23:36

from django.conf import settings
import django.core.files.storage
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import s3.models
import s3.s3utils
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('upload', models.FileField(blank=True, null=True, storage=s3.s3utils.PublicMediaStorage(), upload_to=s3.models.user_file_upload_path)),
                ('local_upload', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.upload_local_path)),
                ('s3_fileName', models.CharField(default='', max_length=100)),
                ('local_fileName', models.CharField(default='', max_length=100)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='s3_publicfile_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PrivateFileJSON',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('s3_fileName', models.CharField(default='', max_length=100)),
                ('local_fileName', models.CharField(default='', max_length=100)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('upload', models.FileField(storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.user_file_upload_path, validators=[django.core.validators.FileExtensionValidator(['json'])])),
                ('local_upload', models.FileField(storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.user_file_upload_path, validators=[django.core.validators.FileExtensionValidator(['json'])])),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='s3_privatefilejson_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PrivateFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('local_upload', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.upload_local_path)),
                ('s3_fileName', models.CharField(default='', max_length=100)),
                ('local_fileName', models.CharField(default='', max_length=100)),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('upload', models.FileField(storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.user_file_upload_path)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='s3_privatefile_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='publicfile',
            constraint=models.CheckConstraint(check=models.Q(models.Q(_negated=True, local_upload__in=['', None]), models.Q(_negated=True, upload__in=['', None]), _connector='OR'), name='has_upload'),
        ),
        migrations.AddConstraint(
            model_name='privatefilejson',
            constraint=models.CheckConstraint(check=models.Q(models.Q(_negated=True, local_upload__in=['', None]), models.Q(_negated=True, upload__in=['', None]), _connector='OR'), name='has_upload'),
        ),
    ]

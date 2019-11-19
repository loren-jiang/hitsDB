# Generated by Django 2.2.6 on 2019-11-15 23:36

import django.core.files.storage
import django.core.validators
from django.db import migrations, models
import s3.models
import s3.s3utils


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0003_auto_20191115_2137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privatefilecsv',
            name='local_upload',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.upload_local_path, validators=[django.core.validators.FileExtensionValidator(['csv'])]),
        ),
        migrations.AlterField(
            model_name='privatefilecsv',
            name='upload',
            field=models.FileField(blank=True, null=True, storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.user_file_upload_path, validators=[django.core.validators.FileExtensionValidator(['csv'])]),
        ),
        migrations.AlterField(
            model_name='privatefilejson',
            name='local_upload',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/'), upload_to=s3.models.upload_local_path, validators=[django.core.validators.FileExtensionValidator(['json'])]),
        ),
        migrations.AlterField(
            model_name='privatefilejson',
            name='upload',
            field=models.FileField(blank=True, null=True, storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.user_file_upload_path, validators=[django.core.validators.FileExtensionValidator(['json'])]),
        ),
        migrations.AddConstraint(
            model_name='privatefilecsv',
            constraint=models.CheckConstraint(check=models.Q(('local_upload__in', ['', None]), ('local_upload__endswith', '.csv'), _connector='OR'), name='endswith_csv'),
        ),
        migrations.AddConstraint(
            model_name='privatefilejson',
            constraint=models.CheckConstraint(check=models.Q(('local_upload__in', ['', None]), ('local_upload__endswith', '.json'), _connector='OR'), name='endswith_json'),
        ),
    ]

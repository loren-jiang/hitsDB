# Generated by Django 2.2.2 on 2019-08-01 17:20

from django.db import migrations, models
import s3.models
import s3.s3utils


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0007_auto_20190801_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privatefile',
            name='upload',
            field=models.FileField(storage=s3.s3utils.PrivateMediaStorage(), upload_to=s3.models.upload_path),
        ),
    ]

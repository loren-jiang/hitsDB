# Generated by Django 2.2.2 on 2019-08-06 23:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0002_auto_20190806_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='wellimage',
            name='well_name',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
    ]

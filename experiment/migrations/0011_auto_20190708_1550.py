# Generated by Django 2.2.2 on 2019-07-08 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0010_auto_20190708_1028'),
    ]

    operations = [
        migrations.AddField(
            model_name='plate',
            name='isCustom',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='plate',
            name='isTemplate',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
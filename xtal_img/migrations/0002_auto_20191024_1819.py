# Generated by Django 2.2.2 on 2019-10-24 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xtal_img', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dropimage',
            name='file_name',
            field=models.CharField(max_length=4),
        ),
    ]

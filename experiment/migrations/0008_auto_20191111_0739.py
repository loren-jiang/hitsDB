# Generated by Django 2.2.6 on 2019-11-11 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0007_auto_20191111_0639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
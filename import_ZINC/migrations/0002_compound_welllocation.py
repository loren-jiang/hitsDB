# Generated by Django 2.2.2 on 2019-08-17 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('import_ZINC', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='compound',
            name='wellLocation',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
    ]

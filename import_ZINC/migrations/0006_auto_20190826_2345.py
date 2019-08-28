# Generated by Django 2.2.2 on 2019-08-26 23:45

from django.db import migrations, models
import import_ZINC.validators


class Migration(migrations.Migration):

    dependencies = [
        ('import_ZINC', '0005_auto_20190819_0452'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compound',
            name='zinc_id',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True, validators=[import_ZINC.validators.validate_prefix('zinc')]),
        ),
    ]

# Generated by Django 2.2.2 on 2019-08-19 04:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('import_ZINC', '0003_auto_20190819_0413'),
    ]

    operations = [
        migrations.RenameField(
            model_name='compound',
            old_name='chemFormula',
            new_name='chemicalFormula',
        ),
    ]

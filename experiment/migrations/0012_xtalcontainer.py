# Generated by Django 2.2.6 on 2019-11-12 23:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0011_experiment_soak_export_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='XtalContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
    ]

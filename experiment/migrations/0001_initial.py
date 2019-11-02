# Generated by Django 2.2.6 on 2019-11-01 23:36

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.utils.timezone
import experiment.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
                ('dateTime', models.DateTimeField(auto_now_add=True)),
                ('protein', models.CharField(max_length=100)),
                ('subwell_locations', django.contrib.postgres.fields.ArrayField(base_field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(3), django.core.validators.MinValueValidator(1)]), default=experiment.models.defaultSubwellLocations, size=3)),
                ('initDataJSON', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            options={
                'get_latest_by': 'dateTime',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('manufacturer', models.CharField(default='', max_length=100)),
                ('date_dispensed', models.DateField(blank=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Plate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('isSource', models.BooleanField(default=False)),
                ('plateIdxExp', models.PositiveIntegerField(blank=True, default=1, null=True)),
                ('dataSheetURL', models.URLField(blank=True, null=True)),
                ('echoCompatible', models.BooleanField(default=False)),
                ('rockMakerId', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('dateTime', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='PlateType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=30, unique=True)),
                ('numCols', models.PositiveIntegerField(default=12, validators=[django.core.validators.MaxValueValidator(99), django.core.validators.MinValueValidator(12)])),
                ('numRows', models.PositiveIntegerField(default=8, validators=[django.core.validators.MaxValueValidator(99), django.core.validators.MinValueValidator(8)])),
                ('isSource', models.BooleanField(default=False)),
                ('numSubwells', models.PositiveIntegerField(default=0)),
                ('xPitch', models.DecimalField(decimal_places=3, max_digits=10)),
                ('yPitch', models.DecimalField(decimal_places=3, max_digits=10)),
                ('plateHeight', models.DecimalField(decimal_places=3, max_digits=10)),
                ('plateWidth', models.DecimalField(decimal_places=3, max_digits=10)),
                ('plateLength', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('wellDepth', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('xOffsetA1', models.DecimalField(decimal_places=3, max_digits=10)),
                ('yOffsetA1', models.DecimalField(decimal_places=3, max_digits=10)),
                ('dataSheetURL', models.URLField(blank=True, null=True)),
                ('echoCompatible', models.BooleanField(blank=True, default=False, null=True)),
                ('isSBS', models.BooleanField(default=True)),
                ('maxResVol', models.DecimalField(decimal_places=0, default=1000, max_digits=10)),
                ('minResVol', models.DecimalField(decimal_places=0, default=50, max_digits=10)),
                ('maxDropVol', models.DecimalField(decimal_places=0, default=5.0, max_digits=10)),
                ('minDropVol', models.DecimalField(decimal_places=0, default=0.5, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('dateTime', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'get_latest_by': 'dateTime',
            },
        ),
        migrations.CreateModel(
            name='Soak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('soakOffsetX', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('soakOffsetY', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('soakVolume', models.DecimalField(decimal_places=2, default=25, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('drop_x', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('drop_y', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('drop_radius', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('well_x', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('well_y', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('well_radius', models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('useSoak', models.BooleanField(default=False)),
                ('saveCount', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='SubWell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=5, validators=[django.core.validators.RegexValidator(message='Enter valid well name', regex='^[A-Z]\\d{2}_[123]$')])),
                ('idx', models.PositiveIntegerField(default=1)),
                ('xPos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('yPos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('maxDropVol', models.DecimalField(decimal_places=0, default=5.0, max_digits=10)),
                ('minDropVol', models.DecimalField(decimal_places=0, default=0.5, max_digits=10)),
                ('protein', models.CharField(default='', max_length=100)),
                ('hasCrystal', models.BooleanField(default=True)),
                ('useSoak', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Well',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=3, validators=[django.core.validators.RegexValidator(message='Enter valid well name', regex='^[A-Z]\\d{2}$')])),
                ('maxResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('minResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('wellIdx', models.PositiveIntegerField(default=0)),
                ('wellRowIdx', models.PositiveIntegerField(default=0)),
                ('wellColIdx', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ('wellRowIdx', 'wellColIdx'),
            },
        ),
    ]

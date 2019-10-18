# Generated by Django 2.2.2 on 2019-10-18 20:49

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import experiment.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('import_ZINC', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                ('plateData', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
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
                ('name', models.CharField(blank=True, default='', max_length=20, null=True)),
                ('isSource', models.BooleanField(default=False)),
                ('plateIdxExp', models.PositiveIntegerField(blank=True, default=1, null=True)),
                ('dataSheetURL', models.URLField(blank=True, null=True)),
                ('echoCompatible', models.BooleanField(blank=True, default=False, null=True)),
                ('rockMakerId', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('experiment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plates', to='experiment.Experiment')),
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
            name='Well',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=4)),
                ('maxResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('minResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('wellIdx', models.PositiveIntegerField(default=0)),
                ('wellRowIdx', models.PositiveIntegerField(default=0)),
                ('wellColIdx', models.PositiveIntegerField(default=0)),
                ('compounds', models.ManyToManyField(blank=True, related_name='wells', to='import_ZINC.Compound')),
                ('plate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wells', to='experiment.Plate')),
                ('screen_ingredients', models.ManyToManyField(blank=True, null=True, related_name='wells', to='experiment.Ingredient')),
            ],
            options={
                'ordering': ('wellIdx',),
                'unique_together': {('plate', 'name')},
            },
        ),
        migrations.CreateModel(
            name='SubWell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idx', models.PositiveIntegerField(default=1)),
                ('xPos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('yPos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('maxDropVol', models.DecimalField(decimal_places=0, default=5.0, max_digits=10)),
                ('minDropVol', models.DecimalField(decimal_places=0, default=0.5, max_digits=10)),
                ('protein', models.CharField(default='', max_length=100)),
                ('hasCrystal', models.BooleanField(default=True)),
                ('willSoak', models.BooleanField(default=True)),
                ('compounds', models.ManyToManyField(blank=True, related_name='subwells', to='import_ZINC.Compound')),
                ('parentWell', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subwells', to='experiment.Well')),
            ],
            options={
                'ordering': ('idx',),
                'unique_together': {('parentWell', 'idx')},
            },
        ),
        migrations.CreateModel(
            name='Soak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transferVol', models.DecimalField(decimal_places=2, default=25, max_digits=10)),
                ('soakOffsetX', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('soakOffsetY', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('targetWellX', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('targetWellY', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('targetWellRadius', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('useSoak', models.BooleanField(default=False)),
                ('dest', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.SubWell')),
                ('experiment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soaks', to='experiment.Experiment')),
                ('src', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.Well')),
                ('transferCompound', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soaks', to='import_ZINC.Compound')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('dateTime', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
                ('collaborators', models.ManyToManyField(blank=True, related_name='collab_projects', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'dateTime',
            },
        ),
        migrations.AddField(
            model_name='plate',
            name='plateType',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plates', to='experiment.PlateType'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='destPlateType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments_dest', to='experiment.PlateType'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='library',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='import_ZINC.Library'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='experiment',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='experiment.Project'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='srcPlateType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments_src', to='experiment.PlateType'),
        ),
        migrations.AlterUniqueTogether(
            name='plate',
            unique_together={('plateIdxExp', 'isSource', 'experiment')},
        ),
    ]

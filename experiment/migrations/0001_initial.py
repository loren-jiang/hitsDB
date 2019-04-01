# Generated by Django 2.1.7 on 2019-03-06 20:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nameInternal', models.CharField(max_length=100)),
                ('chemFormula', models.CharField(default='', max_length=100)),
                ('manufacturer', models.CharField(default='', max_length=100)),
                ('zinc_id', models.CharField(default='', max_length=30)),
                ('smiles', models.CharField(max_length=200, unique=True)),
                ('molWeight', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('concentration', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('chemName', models.CharField(default='', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=300)),
                ('dateTime', models.DateTimeField(auto_now_add=True)),
                ('protein', models.CharField(max_length=30)),
            ],
            options={
                'get_latest_by': 'dateTime',
            },
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(default='', max_length=300)),
                ('groups', models.ManyToManyField(related_name='libraries', to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Plate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='plate_name', max_length=30)),
                ('plateType', models.CharField(max_length=100)),
                ('numCols', models.PositiveIntegerField(default=12)),
                ('numRows', models.PositiveIntegerField(default=8)),
                ('xPitch', models.DecimalField(decimal_places=3, max_digits=10)),
                ('yPitch', models.DecimalField(decimal_places=3, max_digits=10)),
                ('height', models.DecimalField(decimal_places=3, max_digits=10)),
                ('width', models.DecimalField(decimal_places=3, max_digits=10)),
                ('xPosA1', models.DecimalField(decimal_places=3, max_digits=10)),
                ('yPosA1', models.DecimalField(decimal_places=3, max_digits=10)),
                ('isSource', models.BooleanField(default=False)),
                ('isTemplate', models.BooleanField(default=False)),
                ('experiment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plates', to='experiment.Experiment')),
            ],
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
            ],
        ),
        migrations.CreateModel(
            name='Well',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=3)),
                ('maxResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('minResVol', models.DecimalField(decimal_places=0, max_digits=10)),
                ('compounds', models.ManyToManyField(blank=True, null=True, related_name='wells', to='experiment.Compound')),
                ('plate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wells', to='experiment.Plate')),
            ],
        ),
        migrations.AddField(
            model_name='subwell',
            name='well',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subwells', to='experiment.Well'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='library',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='experiment.Library'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='compound',
            name='library',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compounds', to='experiment.Library'),
        ),
    ]

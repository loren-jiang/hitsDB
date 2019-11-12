# Generated by Django 2.2.6 on 2019-11-08 18:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lib', '0001_initial'),
        ('experiment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('s3', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='well',
            name='compound',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='my_wells', to='lib.Compound'),
        ),
        migrations.AddField(
            model_name='well',
            name='compounds',
            field=models.ManyToManyField(blank=True, related_name='wells', to='lib.Compound'),
        ),
        migrations.AddField(
            model_name='well',
            name='plate',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wells', to='experiment.Plate'),
        ),
        migrations.AddField(
            model_name='well',
            name='screen_ingredients',
            field=models.ManyToManyField(blank=True, related_name='wells', to='experiment.Ingredient'),
        ),
        migrations.AddField(
            model_name='subwell',
            name='compounds',
            field=models.ManyToManyField(blank=True, related_name='subwells', to='lib.Compound'),
        ),
        migrations.AddField(
            model_name='subwell',
            name='parentWell',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subwells', to='experiment.Well'),
        ),
        migrations.AddField(
            model_name='soak',
            name='dest',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.SubWell'),
        ),
        migrations.AddField(
            model_name='soak',
            name='experiment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soaks', to='experiment.Experiment'),
        ),
        migrations.AddField(
            model_name='soak',
            name='src',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.Well'),
        ),
        migrations.AddField(
            model_name='soak',
            name='transferCompound',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soaks', to='lib.Compound'),
        ),
        migrations.AddField(
            model_name='project',
            name='collaborators',
            field=models.ManyToManyField(blank=True, related_name='collab_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='editors',
            field=models.ManyToManyField(blank=True, related_name='editor_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='plate',
            name='experiment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plates', to='experiment.Experiment'),
        ),
        migrations.AddField(
            model_name='plate',
            name='plateType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plates', to='experiment.PlateType'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='destPlateType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments_dest', to='experiment.PlateType'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='initData',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiment', to='s3.PrivateFileJSON'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='library',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='lib.Library'),
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
        migrations.AddConstraint(
            model_name='well',
            constraint=models.UniqueConstraint(fields=('plate_id', 'name'), name='unique_well_name_in_plate'),
        ),
        migrations.AddConstraint(
            model_name='subwell',
            constraint=models.UniqueConstraint(fields=('parentWell_id', 'idx'), name='unique_subwell_in_well'),
        ),
        migrations.AlterUniqueTogether(
            name='subwell',
            unique_together={('parentWell', 'idx')},
        ),
        migrations.AddConstraint(
            model_name='plate',
            constraint=models.UniqueConstraint(fields=('plateIdxExp', 'isSource', 'experiment'), name='unique_src_dest_plate_idx'),
        ),
        migrations.AddConstraint(
            model_name='plate',
            constraint=models.CheckConstraint(check=models.Q(('isSource', True), ('isTemplate', True)), name='source_can_only_be_template'),
        ),
    ]
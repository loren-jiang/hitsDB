# Generated by Django 2.2.2 on 2019-09-26 00:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('s3', '0001_initial'),
        ('experiment', '0008_auto_20190823_2106'),
    ]

    operations = [
        migrations.CreateModel(
            name='S3_WellImage',
            fields=[
                ('privatefile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='s3.PrivateFile')),
                ('well_name', models.CharField(max_length=10)),
                ('plate_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='s3_well_images', to='experiment.Plate')),
            ],
            bases=('s3.privatefile',),
        ),
    ]

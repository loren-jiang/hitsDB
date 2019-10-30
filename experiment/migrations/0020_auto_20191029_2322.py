# Generated by Django 2.2.2 on 2019-10-29 23:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0019_auto_20191024_2307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='soak',
            name='dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.SubWell'),
        ),
        migrations.AlterField(
            model_name='soak',
            name='src',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soak', to='experiment.Well'),
        ),
    ]
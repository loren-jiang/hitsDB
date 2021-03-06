# Generated by Django 2.2.6 on 2019-12-16 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0008_soak_dataset'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='soak',
            constraint=models.UniqueConstraint(condition=models.Q(_negated=True, dataset=''), fields=('experiment', 'dataset'), name='unique_dataset_in_experiment'),
        ),
    ]

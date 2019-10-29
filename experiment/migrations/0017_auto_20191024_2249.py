# Generated by Django 2.2.2 on 2019-10-24 22:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0016_auto_20191024_2027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='soak',
            name='drop_radius',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='drop_x',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='drop_y',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='soakOffsetX',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='soakOffsetY',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='soakVolume',
            field=models.DecimalField(decimal_places=2, default=25, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='well_radius',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='well_x',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='soak',
            name='well_y',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]

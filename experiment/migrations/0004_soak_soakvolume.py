# Generated by Django 2.2.2 on 2019-10-24 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0003_auto_20191024_0105'),
    ]

    operations = [
        migrations.AddField(
            model_name='soak',
            name='soakVolume',
            field=models.DecimalField(decimal_places=2, default=25, max_digits=10),
        ),
    ]

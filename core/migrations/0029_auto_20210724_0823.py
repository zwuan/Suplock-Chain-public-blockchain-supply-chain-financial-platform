# Generated by Django 3.1 on 2021-07-24 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20210724_0755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tokenb',
            name='interest',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

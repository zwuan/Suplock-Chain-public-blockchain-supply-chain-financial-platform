# Generated by Django 3.1 on 2021-07-01 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='public_address',
            field=models.CharField(default=1, max_length=42),
            preserve_default=False,
        ),
    ]

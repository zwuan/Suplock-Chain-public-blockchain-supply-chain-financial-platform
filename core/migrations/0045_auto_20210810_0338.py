# Generated by Django 3.1.7 on 2021-08-10 03:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_auto_20210810_0323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tranche',
            name='accu_earning',
            field=models.CharField(default='0', max_length=100, null=True),
        ),
    ]
# Generated by Django 3.1.7 on 2021-08-10 03:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_loanpayable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tranche',
            name='accu_earning',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

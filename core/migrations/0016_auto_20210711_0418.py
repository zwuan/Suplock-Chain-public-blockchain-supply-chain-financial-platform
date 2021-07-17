# Generated by Django 3.1 on 2021-07-11 04:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20210711_0408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company_orders',
            name='rate',
            field=models.FloatField(blank=True, choices=[(0.03, '3%'), (0.04, '4%'), (0.05, '5%'), (0.06, '6%'), (0.07, '7%'), (0.08, '8%'), (0.09, '9%'), (0.1, '10%'), (0.11, '11%'), (0.12, '12%'), (0.13, '13%')], null=True),
        ),
    ]
# Generated by Django 3.1.7 on 2021-07-18 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20210718_0748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company_orders',
            name='already_loan',
            field=models.DecimalField(blank=True, decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='company_orders',
            name='already_transfer',
            field=models.DecimalField(blank=True, decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='company_orders',
            name='tokenB_balance',
            field=models.DecimalField(blank=True, decimal_places=0, default=0, max_digits=12),
        ),
    ]
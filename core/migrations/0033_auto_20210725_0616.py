# Generated by Django 3.1 on 2021-07-25 06:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_company_orders_quantity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company_orders',
            old_name='Quantity',
            new_name='quantity',
        ),
    ]
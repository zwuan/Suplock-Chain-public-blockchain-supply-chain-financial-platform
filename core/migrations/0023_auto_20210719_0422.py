# Generated by Django 3.1.7 on 2021-07-19 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20210719_0323'),
    ]

    operations = [
        migrations.AddField(
            model_name='company_orders',
            name='transactionHash',
            field=models.CharField(blank=True, max_length=66, null=True),
        ),
        migrations.AddField(
            model_name='deposit',
            name='transactionHash',
            field=models.CharField(blank=True, max_length=66, null=True),
        ),
        migrations.AddField(
            model_name='tokenb',
            name='transactionHash',
            field=models.CharField(blank=True, max_length=66, null=True),
        ),
    ]

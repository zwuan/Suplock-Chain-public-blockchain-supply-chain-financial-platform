# Generated by Django 3.1.7 on 2021-07-19 14:53

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20210719_0422'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tokenA_amount', models.CharField(blank=True, max_length=100, null=True)),
                ('tokenA_time', models.DateTimeField(default=datetime.datetime.now)),
                ('transactionHash', models.CharField(blank=True, max_length=66, null=True)),
                ('tokenA_company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokenA_company', to='core.company')),
            ],
        ),
    ]

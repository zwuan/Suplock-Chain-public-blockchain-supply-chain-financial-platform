# Generated by Django 3.1 on 2021-09-06 14:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_auto_20210901_0942'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dividend_record',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.IntegerField(blank=True, null=True)),
                ('principle_interest', models.TextField(blank=True, null=True)),
                ('tranche', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dividend_record', to='core.tokenb')),
            ],
        ),
    ]

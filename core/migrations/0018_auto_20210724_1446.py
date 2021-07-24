# Generated by Django 3.1.2 on 2021-07-24 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20210711_0732'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='capital',
            field=models.DecimalField(decimal_places=0, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='chairman',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='company_location',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='company_type',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='establish_date',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='responsible_person',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='supervisor',
            field=models.CharField(blank=True, max_length=42, null=True),
        ),
    ]

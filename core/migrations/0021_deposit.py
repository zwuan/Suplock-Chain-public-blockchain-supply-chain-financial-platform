# Generated by Django 3.1.7 on 2021-07-18 12:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20210718_1150'),
    ]

    operations = [
        migrations.CreateModel(
            name='Deposit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deposit_amount', models.CharField(blank=True, max_length=100, null=True)),
                ('deposit_time', models.DateTimeField(auto_now_add=True)),
                ('deposit_company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deposit_company', to='core.company')),
            ],
        ),
    ]

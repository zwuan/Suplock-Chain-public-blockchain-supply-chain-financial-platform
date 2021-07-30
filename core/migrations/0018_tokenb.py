# Generated by Django 3.1.7 on 2021-07-18 07:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20210711_0732'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(blank=True, null=True)),
                ('class_type', models.IntegerField(blank=True, choices=[(1, '應收'), (2, '訂單'), (3, '移轉'), (4, '貸款')], null=True)),
                ('token_id', models.PositiveBigIntegerField(blank=True, null=True)),
                ('interest', models.FloatField(blank=True, null=True)),
                ('date_span', models.IntegerField(blank=True, null=True)),
                ('transfer_count', models.IntegerField(blank=True, null=True)),
                ('curr_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='curr_company', to='core.company')),
                ('initial_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='initial_order', to='core.company_orders')),
                ('pre_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pre_company', to='core.company')),
            ],
        ),
    ]
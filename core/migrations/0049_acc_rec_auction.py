# Generated by Django 3.1 on 2021-08-21 06:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_invest_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='acc_rec_auction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opening_price', models.IntegerField(blank=True, null=True)),
                ('state', models.IntegerField(blank=True, choices=[(1, '出售中'), (2, '成交')], null=True)),
                ('core_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_company', to='core.company')),
                ('pre_own', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pre_own', to='core.company')),
                ('tokenB', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='acc_recB_id', to='core.tokenb')),
            ],
        ),
    ]
# Generated by Django 5.2.4 on 2025-07-15 12:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ParkingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barrier_open', models.BooleanField(default=False)),
                ('last_data_clear', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Parking Settings',
                'verbose_name_plural': 'Parking Settings',
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_plate', models.CharField(max_length=20, unique=True)),
                ('is_monthly_pass_holder', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ParkingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_number', models.CharField(max_length=20, unique=True)),
                ('entry_time', models.DateTimeField(auto_now_add=True)),
                ('exit_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('parked', 'Currently Parked'), ('exited', 'Exited')], default='parked', max_length=10)),
                ('pass_expires', models.DateTimeField(blank=True, null=True)),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.vehicle')),
            ],
        ),
    ]

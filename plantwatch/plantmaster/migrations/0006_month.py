# Generated by Django 3.0.5 on 2020-05-11 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plantmaster', '0005_power'),
    ]

    operations = [
        migrations.CreateModel(
            name='Month',
            fields=[
                ('monthid', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('power', models.IntegerField()),
            ],
            options={
                'db_table': 'month',
                'managed': False,
            },
        ),
    ]

# Generated by Django 4.0.4 on 2022-04-15 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webFilter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='rank',
            field=models.FloatField(default=0),
        ),
    ]
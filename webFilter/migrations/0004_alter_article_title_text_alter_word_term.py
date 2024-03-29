# Generated by Django 4.0.4 on 2022-04-16 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webFilter', '0003_alter_article_abstract'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='title_text',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='word',
            name='term',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]

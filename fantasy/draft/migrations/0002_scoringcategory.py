# Generated by Django 2.2.4 on 2019-08-31 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draft', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoringCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(max_length=50)),
                ('category_abbreviation', models.CharField(max_length=5)),
            ],
        ),
    ]
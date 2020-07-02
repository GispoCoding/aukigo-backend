# Generated by Django 3.0.7 on 2020-06-29 13:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('datahub', '0009_auto_20200626_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='VectorTileBasemap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('attribution', models.CharField(blank=True,
                                                 help_text='OPTIONAL. Contains an attribution to be displayed when the map is shown to a user. Implementations MAY decide to treat this as HTML or literal text',
                                                 max_length=200, null=True)),
                ('url', models.URLField(help_text='Vector tile url', max_length=1000)),
                ('api_key', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WMTSBasemap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('attribution', models.CharField(blank=True,
                                                 help_text='OPTIONAL. Contains an attribution to be displayed when the map is shown to a user. Implementations MAY decide to treat this as HTML or literal text',
                                                 max_length=200, null=True)),
                ('url', models.URLField(help_text='Capabilities xml url', max_length=500)),
                ('layer', models.CharField(max_length=100)),
                ('tile_matrix_set', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

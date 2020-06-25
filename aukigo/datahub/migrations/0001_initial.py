# Generated by Django 3.0.7 on 2020-06-17 10:04

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AreaOfInterest',
            fields=[
                ('name', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('bbox', django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('tags',
                 django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True,
                                                           null=True, size=None)),
                ('is_osm_layer', models.BooleanField()),
                ('areas', models.ManyToManyField(blank=True, to='datahub.AreaOfInterest')),
            ],
        ),
        migrations.CreateModel(
            name='OsmPolygon',
            fields=[
                ('osmid', models.BigIntegerField(primary_key=True, serialize=False)),
                ('tags', django.contrib.postgres.fields.jsonb.JSONField()),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('layers', models.ManyToManyField(blank=True, to='datahub.Layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OsmPoint',
            fields=[
                ('osmid', models.BigIntegerField(primary_key=True, serialize=False)),
                ('tags', django.contrib.postgres.fields.jsonb.JSONField()),
                ('geom', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('layers', models.ManyToManyField(blank=True, to='datahub.Layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OsmLine',
            fields=[
                ('osmid', models.BigIntegerField(primary_key=True, serialize=False)),
                ('tags', django.contrib.postgres.fields.jsonb.JSONField()),
                ('geom', django.contrib.gis.db.models.fields.LineStringField(srid=4326)),
                ('layers', models.ManyToManyField(blank=True, to='datahub.Layer')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

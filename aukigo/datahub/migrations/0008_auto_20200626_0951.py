# Generated by Django 3.0.7 on 2020-06-26 06:51

import django_better_admin_arrayfield.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('datahub', '0007_auto_20200626_0916'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='osmlayer',
            name='is_osm_layer',
        ),
        migrations.AlterField(
            model_name='osmlayer',
            name='tags',
            field=django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.CharField(max_length=200),
                                                                          blank=True,
                                                                          help_text='Allowed formats: key=val, key~regex, ~keyregex~regex, key=*, key',
                                                                          null=True, size=None),
        ),
    ]
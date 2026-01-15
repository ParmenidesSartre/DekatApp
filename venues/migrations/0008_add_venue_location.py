# Generated manually for adding venue location fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0007_state_move_merchants_to_merchants_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='venue',
            name='latitude',
            field=models.FloatField(blank=True, help_text='Venue latitude for location-based search', null=True),
        ),
        migrations.AddField(
            model_name='venue',
            name='longitude',
            field=models.FloatField(blank=True, help_text='Venue longitude for location-based search', null=True),
        ),
        migrations.AddField(
            model_name='venue',
            name='address',
            field=models.TextField(blank=True, help_text='Full address of the venue'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_event_registration_deadline"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
    ]

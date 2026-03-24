from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0009_participant_is_paid_participant_paid_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="registration_deadline",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

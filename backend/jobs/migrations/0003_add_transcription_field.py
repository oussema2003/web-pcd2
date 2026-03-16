from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_add_audio_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidature",
            name="transcription",
            field=models.TextField(null=True, blank=True),
        ),
    ]


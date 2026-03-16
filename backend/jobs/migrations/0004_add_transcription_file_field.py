from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_add_transcription_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidature",
            name="transcription_file",
            field=models.FileField(
                upload_to="candidatures/transcriptions/", null=True, blank=True
            ),
        ),
    ]


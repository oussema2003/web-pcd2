from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidature",
            name="audio",
            field=models.FileField(
                upload_to="candidatures/audio/", null=True, blank=True
            ),
        ),
    ]


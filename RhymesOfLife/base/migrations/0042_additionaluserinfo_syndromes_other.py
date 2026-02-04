from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0041_help_request_status_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="additionaluserinfo",
            name="syndromes_other",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]

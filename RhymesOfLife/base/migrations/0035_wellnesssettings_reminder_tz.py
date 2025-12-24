from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0034_additionaluserinfo_banned_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="wellnesssettings",
            name="reminder_tz",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]

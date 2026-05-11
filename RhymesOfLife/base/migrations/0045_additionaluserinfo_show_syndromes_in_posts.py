from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0044_additionaluserinfo_data_processing_consent_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="additionaluserinfo",
            name="show_syndromes_in_posts",
            field=models.BooleanField(default=False),
        ),
    ]

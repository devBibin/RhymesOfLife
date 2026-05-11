from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0043_additionaluserinfo_syndrome_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="additionaluserinfo",
            name="data_processing_consent_type",
            field=models.CharField(
                blank=True,
                choices=[("user", "User"), ("expert", "Expert")],
                default="",
                max_length=16,
            ),
        ),
    ]

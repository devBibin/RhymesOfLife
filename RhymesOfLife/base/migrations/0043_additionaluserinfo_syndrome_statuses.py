import django.contrib.postgres.fields
from django.db import migrations, models


def migrate_legacy_syndrome_statuses(apps, schema_editor):
    AdditionalUserInfo = apps.get_model("base", "AdditionalUserInfo")
    for info in AdditionalUserInfo.objects.all().iterator():
        selected = list(getattr(info, "syndromes", None) or [])
        genetic = set(getattr(info, "confirmed_syndromes", None) or [])
        statuses = {}

        for code in selected:
            if code in genetic:
                statuses[code] = ["genetically_confirmed"]
            else:
                statuses[code] = ["doctor_unconfirmed"]

        info.syndrome_statuses = statuses
        info.save(update_fields=["syndrome_statuses"])


def clear_syndrome_statuses(apps, schema_editor):
    AdditionalUserInfo = apps.get_model("base", "AdditionalUserInfo")
    AdditionalUserInfo.objects.update(syndrome_statuses={})


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0042_additionaluserinfo_syndromes_other"),
    ]

    operations = [
        migrations.AlterField(
            model_name="additionaluserinfo",
            name="syndromes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=32),
                blank=True,
                default=list,
                size=8,
            ),
        ),
        migrations.AlterField(
            model_name="additionaluserinfo",
            name="confirmed_syndromes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=32),
                blank=True,
                default=list,
                size=8,
            ),
        ),
        migrations.AddField(
            model_name="additionaluserinfo",
            name="syndrome_statuses",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(migrate_legacy_syndrome_statuses, clear_syndrome_statuses),
    ]

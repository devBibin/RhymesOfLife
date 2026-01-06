from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def backfill_status(apps, schema_editor):
    HelpRequest = apps.get_model("base", "HelpRequest")
    for item in HelpRequest.objects.all():
        if getattr(item, "is_processed", False):
            item.status = "done"
            item.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0040_rename_base_patien_patient_7c58ab_idx_base_patien_patient_eb1618_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="helprequest",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="help_requests", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="status",
            field=models.CharField(choices=[("open", "Open"), ("in_work", "In work"), ("done", "Processed")], db_index=True, default="open", max_length=16, verbose_name="status"),
        ),
        migrations.RunPython(backfill_status, migrations.RunPython.noop),
    ]

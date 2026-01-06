from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0036_medicationentry"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientAccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("denied", "Denied")], db_index=True, default="pending", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("doctor", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="access_requests_sent", to="base.additionaluserinfo")),
                ("patient", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="access_requests_received", to="base.additionaluserinfo")),
            ],
            options={
                "verbose_name": "Access request",
                "verbose_name_plural": "Access requests",
                "unique_together": {("patient", "doctor")},
            },
        ),
        migrations.AddIndex(
            model_name="patientaccessrequest",
            index=models.Index(fields=["patient", "status"], name="base_patien_patient_7c58ab_idx"),
        ),
        migrations.AddIndex(
            model_name="patientaccessrequest",
            index=models.Index(fields=["doctor", "status"], name="base_patien_doctor_86db2f_idx"),
        ),
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(choices=[("FOLLOW", "Follow"), ("EXAM_COMMENT", "ExamComment"), ("RECOMMENDATION", "Recommendation"), ("ADMIN_MESSAGE", "AdminMessage"), ("SYSTEM_MESSAGE", "SystemMessage"), ("ACCESS_REQUEST", "AccessRequest"), ("ACCESS_GRANTED", "AccessGranted"), ("ACCESS_DENIED", "AccessDenied")], db_index=True, max_length=50),
        ),
    ]

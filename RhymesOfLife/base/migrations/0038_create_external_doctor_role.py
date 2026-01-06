from django.db import migrations


EXTERNAL_DOCTOR = "external_doctor"
BASE_APP = "base"

EXTERNAL_DOCTOR_PERMS = [
    "view_patient_list",
]


def create_external_doctor_role(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    perms = list(
        Permission.objects.filter(
            content_type__app_label=BASE_APP,
            codename__in=EXTERNAL_DOCTOR_PERMS,
        )
    )
    group, _ = Group.objects.get_or_create(name=EXTERNAL_DOCTOR)
    group.permissions.set(perms)


def remove_external_doctor_role(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=EXTERNAL_DOCTOR).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0037_access_requests"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(create_external_doctor_role, remove_external_doctor_role),
    ]

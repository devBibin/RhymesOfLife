from django.db import migrations


DOCTOR = "doctor"
VOLUNTEER = "volunteer"
USER = "user"

BASE_APP = "base"

DOCTOR_PERMS = [
    "view_patient_list",
    "view_patient_exams",
    "modify_patient_exams",
    "comment_exams",
    "moderate_exam_comments",
    "view_recommendations",
    "write_recommendations",
]

VOLUNTEER_PERMS = [
    "view_help_requests",
    "process_help_requests",
]

USER_PERMS = [
    # keep empty or add basic perms if needed later
]


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # collect Permission objects by codenames within app "base"
    def perms_by_codenames(codenames):
        return list(
            Permission.objects.filter(
                content_type__app_label=BASE_APP,
                codename__in=codenames,
            )
        )

    doctor_group, _ = Group.objects.get_or_create(name=DOCTOR)
    volunteer_group, _ = Group.objects.get_or_create(name=VOLUNTEER)
    user_group, _ = Group.objects.get_or_create(name=USER)

    doctor_group.permissions.set(perms_by_codenames(DOCTOR_PERMS))
    volunteer_group.permissions.set(perms_by_codenames(VOLUNTEER_PERMS))
    user_group.permissions.set(perms_by_codenames(USER_PERMS))


def remove_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=[DOCTOR, VOLUNTEER, USER]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0029_alter_additionaluserinfo_options_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(create_roles, remove_roles),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0038_create_external_doctor_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="helprequest",
            name="birth_date",
            field=models.DateField(blank=True, null=True, verbose_name="birth date"),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="city",
            field=models.CharField(blank=True, max_length=120, verbose_name="city"),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="gen",
            field=models.TextField(blank=True, verbose_name="gen"),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="medications",
            field=models.TextField(blank=True, verbose_name="medications"),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="phone",
            field=models.CharField(blank=True, max_length=32, verbose_name="phone"),
        ),
        migrations.AddField(
            model_name="helprequest",
            name="syndrome",
            field=models.CharField(blank=True, max_length=120, verbose_name="syndrome"),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    PhoneVerification = apps.get_model('base', 'PhoneVerification')
    AdditionalUserInfo = apps.get_model('base', 'AdditionalUserInfo')
    for pv in PhoneVerification.objects.all():
        user_id = getattr(pv, 'user_id', None)
        if user_id:
            info = AdditionalUserInfo.objects.filter(user_id=user_id).first()
            if info:
                pv.user_info_id = info.id
                pv.save(update_fields=['user_info_id'])


def backwards(apps, schema_editor):
    PhoneVerification = apps.get_model('base', 'PhoneVerification')
    for pv in PhoneVerification.objects.select_related('user_info'):
        if pv.user_info_id:
            pv.user_id = pv.user_info.user_id
            pv.save(update_fields=['user_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_phoneverification_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='phoneverification',
            name='user_info',
            field=models.OneToOneField(
                related_name='phone_verification',
                on_delete=django.db.models.deletion.CASCADE,
                to='base.additionaluserinfo',
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='phoneverification',
            name='user_info',
            field=models.OneToOneField(
                related_name='phone_verification',
                on_delete=django.db.models.deletion.CASCADE,
                to='base.additionaluserinfo',
            ),
        ),
        migrations.RemoveField(
            model_name='phoneverification',
            name='user',
        ),
    ]

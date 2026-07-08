from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0045_additionaluserinfo_show_syndromes_in_posts"),
        ("blog", "0017_blogpage_is_hidden"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpage",
            name="subscribers_notified_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Subscribers notified at"),
        ),
        migrations.CreateModel(
            name="ArticleSubscriptionSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(db_index=True, default=False)),
                ("site_notifications_enabled", models.BooleanField(db_index=True, default=True)),
                ("tg_notifications_enabled", models.BooleanField(db_index=True, default=True)),
                ("email_notifications_enabled", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user_info",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="article_subscription_settings",
                        to="base.additionaluserinfo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Article subscription settings",
                "verbose_name_plural": "Article subscription settings",
                "indexes": [
                    models.Index(fields=["enabled"], name="blog_articl_enabled_5418df_idx"),
                    models.Index(fields=["site_notifications_enabled"], name="blog_articl_site_no_20e86c_idx"),
                    models.Index(fields=["tg_notifications_enabled"], name="blog_articl_tg_noti_6f46f7_idx"),
                    models.Index(fields=["email_notifications_enabled"], name="blog_articl_email__f92e2d_idx"),
                ],
            },
        ),
    ]

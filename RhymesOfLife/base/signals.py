from django.db.models.signals import post_save
from django.dispatch import receiver
from wiki.models import Article
from .models import CustomArticle

@receiver(post_save, sender=Article)
def create_custom_article_fields(sender, instance, created, **kwargs):
    if created:
        CustomArticle.objects.create(article=instance)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from wagtail.models import Page
from wagtail.images.models import Image
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import BlogPage, BlogIndexPage, ArticleLike, ArticleComment


@login_required
@require_http_methods(["GET", "POST"])
def create_article_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        intro = request.POST.get('intro', '').strip()
        body = request.POST.get('body', '').strip()
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        main_image_file = request.FILES.get('main_image')

        try:
            if not hasattr(request.user, 'additional_info'):
                raise ValidationError("Профиль пользователя не найден")

            if not title or not body:
                raise ValidationError("Заголовок и контент статьи обязательны")

            main_image = None
            if main_image_file:
                main_image = Image.objects.create(
                    title=f"{title} — главное изображение",
                    file=main_image_file,
                    uploaded_by_user=request.user
                )

            root = Page.get_first_root_node()
            if not root:
                raise Exception("Wagtail root page не найден. Убедитесь, что база инициализирована.")

            parent = BlogIndexPage.objects.first()
            if not parent:
                parent = BlogIndexPage(title="Блог", slug="blog")
                root.add_child(instance=parent)
                parent.save_revision().publish()

            page = BlogPage(
                title=title,
                slug=slugify(title),
                date=timezone.now(),
                intro=intro,
                author=request.user.additional_info,
                main_image=main_image,
                body=body,
            )

            parent.add_child(instance=page)
            page.tags.add(*tags)
            page.save_revision().publish()

            return redirect(page.url)

        except ValidationError as ve:
            return render(request, 'blog/create_article.html', {
                'error': str(ve),
                'title': title,
                'intro': intro,
                'body': body,
                'tags': ', '.join(tags)
            })

        except Exception as e:
            return render(request, 'blog/create_article.html', {
                'error': f"Ошибка сервера: {str(e)}",
                'title': title,
                'intro': intro,
                'body': body,
                'tags': ', '.join(tags)
            })

    return render(request, 'blog/create_article.html')


# EDITING ARTICLE
@login_required
@require_http_methods(["GET", "POST"])
def edit_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific

    if not page.is_editable_by(request.user):
        return HttpResponseForbidden("Недостаточно прав.")

    if request.method == 'POST':
        try:
            page.title = request.POST.get('title', page.title).strip()
            page.intro = request.POST.get('intro', page.intro).strip()
            page.body = request.POST.get('body', page.body).strip()
            tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
            page.tags.set(*tags)

            if 'main_image' in request.FILES:
                if page.main_image:
                    page.main_image.delete()
                page.main_image = Image.objects.create(
                    title=f"{page.title} — главное изображение",
                    file=request.FILES['main_image'],
                    uploaded_by_user=request.user
                )
            elif request.POST.get('main_image-clear') == 'on':
                if page.main_image:
                    page.main_image.delete()
                    page.main_image = None

            page.save_revision().publish()
            return redirect(page.url)

        except Exception as e:
            return render(request, 'blog/edit_article.html', {
                'page': page,
                'page_tags': ', '.join(page.tags.names()),
                'error': str(e)
            })

    return render(request, 'blog/edit_article.html', {'page': page})


# DELETE
@login_required
@require_POST
def delete_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    if not page.is_editable_by(request.user):
        return HttpResponseForbidden("Недостаточно прав.")

    page.is_deleted = True
    page.save_revision().publish()
    return redirect('blog_index')


# LIKE
@login_required
@require_POST
def like_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    user_info = request.user.additional_info

    like, created = ArticleLike.objects.get_or_create(
        author=user_info,
        article=page,
        defaults={'is_active': True}
    )

    if not created:
        like.is_active = not like.is_active
        like.save()

    page.likes_count = ArticleLike.objects.filter(article=page, is_active=True).count()
    page.save(update_fields=["likes_count"])

    return JsonResponse({
        'liked': like.is_active,
        'like_count': page.likes_count
    })


# COMMENT
@login_required
@require_POST
def comment_article_view(request, page_id):
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Комментарий не может быть пустым'}, status=400)

    page = get_object_or_404(BlogPage, id=page_id).specific
    user_info = request.user.additional_info

    comment = ArticleComment.objects.create(article=page, author=user_info, text=text)

    page.comments_count = ArticleComment.objects.filter(article=page).count()
    page.save(update_fields=["comments_count"])

    return JsonResponse({
        'username': user_info.first_name or request.user.username,
        'avatar': user_info.avatar.url if user_info.avatar else '',
        'text': comment.text,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        'comment_count': page.comments_count
    })

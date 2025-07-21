from datetime import datetime
from time import localtime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from .forms import ProfileForm
from django.http import JsonResponse
from wiki.models.article import Article
from .models import *
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import magic
import os
import base64
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import RegisterForm
from django.http import HttpResponse


# =================== REGISTRATION / LOGIN / LOGOUT REGION ===================

def register_view(request):
    context = {"values": {}}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        context["values"] = {"username": username, "email": email}

        # Валидация
        if not username or not email or not password1:
            context["error"] = "Please fill in all fields."
        elif password1 != password2:
            context["error"] = "Passwords don't match."
        elif User.objects.filter(username=username).exists():
            context["error"] = "A user with that name already exists."
        elif User.objects.filter(email=email).exists():
            context["error"] = "The email has already been registered."
        else:
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password1)
            )
            # Связанный профиль
            user.additional_info.ready_for_verification = True
            user.additional_info.save()

            messages.success(request, 'Registration was successful! An email confirmation will be sent within a minute.')
            return redirect('login')

    return render(request, 'base/register.html', context)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'base/login.html', {'form': form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect('login')


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.additional_info.is_verified = True
        user.additional_info.save()

        login(request, user)
        return redirect('my_profile')
    else:
        return render(request, 'base/verification_failed.html')



@login_required
def request_verification_view(request):
    user = request.user
    user.additional_info.ready_for_verification = True
    user.additional_info.save()
    messages.success(request, "A verification email has been sent to your email. Please confirm your account.")
    return redirect('home')


@login_required
def home_view(request):
    user = request.user
    return render(request, 'base/home.html', {
        'user': user,
        'show_verification_notice': not user.additional_info.is_verified})


@login_required
def resend_verification_view(request):
    user = request.user
    if user.additional_info.is_verified:
        messages.info(request, "You are already verified.")
    elif user.additional_info.ready_for_verification:
        messages.info(request, "A verification email is already in the queue.")
    else:
        user.additional_info.ready_for_verification = True
        user.additional_info.save()
        messages.success(request, "The verification email will be sent again within a minute.")
    return redirect('home')


# =================== END REGISTRATION / LOGIN / LOGOUT REGION ===================


# =================== PROFILE REGION ===================
@login_required
def profile_edit_view(request):
    info = request.user.additional_info

    syndrome_choices = ["Синдром 1", "Синдром 2", "Синдром 3"]

    if request.method == 'POST':
        info.first_name = request.POST.get('first_name', '').strip()
        info.last_name = request.POST.get('last_name', '').strip()
        info.email = request.POST.get('email', '').strip()
        info.syndrome = request.POST.get('syndrome', '').strip()
        info.birth_date = request.POST.get('birth_date') or None

        image = request.FILES.get('avatar')
        if image:
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
            if image.size > MAX_FILE_SIZE:
                return JsonResponse({'success': False, 'error': 'Файл слишком большой (макс. 10MB)'})

            image_data = image.read()
            try:
                img = Image.open(BytesIO(image_data))
                img.verify()
                img = Image.open(BytesIO(image_data))
            except UnidentifiedImageError:
                return JsonResponse({'success': False, 'error': 'Файл не является изображением'})
            except Exception:
                return JsonResponse({'success': False, 'error': 'Ошибка обработки изображения'})

            MAX_WIDTH, MAX_HEIGHT = 10000, 10000
            if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                return JsonResponse({'success': False, 'error': 'Изображение слишком большое (макс 10K x 10K)'})

            ALLOWED_FORMATS = ('JPEG', 'PNG', 'WEBP', "MPO", "HEIC")
            if img.format not in ALLOWED_FORMATS:
                return JsonResponse({'success': False, 'error': f'Формат {img.format} не поддерживается'})

            info.avatar.save(image.name, BytesIO(image_data))

        info.save()
        return JsonResponse({'success': True})

    return render(request, 'base/profile_edit.html', {'info': info, 'syndrome_choices': syndrome_choices})



@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
        editable = (user == request.user)
    else:
        user = request.user
        editable = True

    info = user.additional_info

    return render(request, 'base/profile.html', {
        'user_profile': user,
        'info': info,
        'editable': editable
    })

# =================== END PROFILE REGION ===================

# =================== WIKI REGION ===================

@require_POST
@login_required
def toggle_like(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    user_info = request.user.additional_info

    custom_article, _ = CustomArticle.objects.get_or_create(article=article)

    like, created = ArticleLike.objects.get_or_create(
        user_info=user_info,
        custom_article=custom_article,
        defaults={'is_active': True}
    )

    if not created:
        like.is_active = not like.is_active
        like.save()

    if like.is_active:
        custom_article.likes_count += 1
    else:
        custom_article.likes_count = max(0, custom_article.likes_count - 1)

    custom_article.save()

    return JsonResponse({
        'liked': like.is_active,
        'total_likes': custom_article.likes_count
    })


@require_POST
@login_required
def post_comment(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    custom_article = getattr(article, 'custom_fields', None)

    if not custom_article:
        return JsonResponse({'error': 'CustomArticle not found for this article'}, status=400)

    text = request.POST.get('comment', '').strip()
    if not text:
        return JsonResponse({'error': 'Comment can not be blank.'}, status=400)

    comment = ArticleComment.objects.create(
        user_info=request.user.additional_info,
        custom_article=custom_article,
        text=text
    )

    custom_article.comments_count = custom_article.comments.count()
    custom_article.save(update_fields=["comments_count"])


    return JsonResponse({
        'username': request.user.username,
        'comment': {
            'id': comment.id,
            'text': comment.text,
            'created_at': comment.created_at.isoformat()
        }
    })

@require_GET
def get_article_comments(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    custom_article = getattr(article, 'custom_fields', None)

    if not custom_article:
        return JsonResponse({'error': 'CustomArticle not found'}, status=404)

    comments = custom_article.comments.select_related('user_info__user').order_by('created_at')

    comments_data = [
        {
            'username': comment.user_info.user.username,
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'created_at': comment.created_at.isoformat()
            }

        }
        for comment in comments
    ]

    print(comments_data)   
    return JsonResponse({'comments': comments_data})

# =================== END WIKI REGION ===================

# =================== MY DOCUMENTS REGION ===================
@login_required
def my_documents_view(request):
    user_info = request.user.additional_info

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        description = request.POST.get('description', '')
        exam_date_str = request.POST.get('exam_date')

        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Неверный формат даты'})

        if not files:
            return JsonResponse({'status': 'error', 'message': 'Файлы не выбраны'})

        MAX_SIZE = 20 * 1024 * 1024  # 20 MB
        ALLOWED_EXT = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        ALLOWED_MIME = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]

        exam = MedicalExam.objects.create(
            user_info=user_info,
            exam_date=exam_date,
            description=description
        )

        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_EXT:
                exam.delete()
                return JsonResponse({'status': 'error', 'message': f'Файл {f.name} имеет недопустимое расширение'})

            if f.size > MAX_SIZE:
                exam.delete()
                return JsonResponse({'status': 'error', 'message': f'Файл {f.name} превышает лимит в 20MB'})

            mime = magic.from_buffer(f.read(1024), mime=True)
            f.seek(0)
            if mime not in ALLOWED_MIME:
                if not (ext == '.docx' and mime == 'application/zip'):
                    exam.delete()
                    return JsonResponse({'status': 'error', 'message': f'Файл {f.name} имеет недопустимый тип: {mime}'})


            try:
                if mime.startswith("image/"):
                    image_data = f.read()
                    f.seek(0)
                    img = Image.open(BytesIO(image_data))
                    img.verify()
                    img = Image.open(BytesIO(image_data))
                    MAX_WIDTH, MAX_HEIGHT = 10000, 10000
                    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                        exam.delete()
                        return JsonResponse({'status': 'error', 'message': f'Изображение {f.name} слишком большое'})
            except UnidentifiedImageError:
                exam.delete()
                return JsonResponse({'status': 'error', 'message': f'{f.name} не является изображением'})
            except Exception:
                exam.delete()
                return JsonResponse({'status': 'error', 'message': f'Ошибка при проверке файла {f.name}'})

            MedicalDocument.objects.create(exam=exam, file=f)

        return JsonResponse({'status': 'ok'})

    exams = user_info.medical_exams.all().prefetch_related('documents')
    return render(request, 'base/my_documents.html', {
        'exams': exams
    })

@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def exam_detail_api(request, exam_id):
    exam = get_object_or_404(MedicalExam, id=exam_id, user_info=request.user.additional_info)

    if request.method == "GET":
        return JsonResponse({
            "id": exam.id,
            "exam_date": exam.exam_date.strftime("%Y-%m-%d"),
            "description": exam.description,
            "documents": [
                {"id": doc.id, "name": os.path.basename(doc.file.name), "url": doc.file.url}
                for doc in exam.documents.all()
            ]
        })

    if request.method == "PUT":
        try:
            exam.exam_date = datetime.strptime(request.POST.get("exam_date", ""), "%Y-%m-%d").date()
            exam.description = request.POST.get("description", "")
            exam.save()

            for file in request.FILES.getlist("files"):
                MedicalDocument.objects.create(exam=exam, file=file)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    if request.method == "DELETE":
        exam.delete()
        return JsonResponse({"status": "ok"})
    
@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_document_api(request, doc_id):
    document = get_object_or_404(MedicalDocument, id=doc_id, exam__user_info=request.user.additional_info)
    document.file.delete(save=False)
    document.delete()
    return JsonResponse({"status": "ok"})

# =================== DOCTORS SEGMENT ====================

@login_required
def patients_list_view(request):
    if not request.user.is_staff:
        return redirect("home")

    query = request.GET.get("q", "").strip()
    all_patients = AdditionalUserInfo.objects.select_related("user")

    if query:
        all_patients = all_patients.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

    paginator = Paginator(all_patients.order_by("last_name", "first_name"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "base/patients_list.html", {
        "query": query,
        "page_obj": page_obj,
        "patients": page_obj.object_list
    })

@login_required
def patient_exams_view(request, user_id):
    if not request.user.is_staff:
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    user_info = getattr(user, "additional_info", None)
    exams = user_info.medical_exams.prefetch_related("documents") if user_info else []

    return render(request, "base/patient_exams.html", {
        "patient": user,
        "exams": exams
    })
# =================== END MY DOCUMENTS REGION ===================
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from .forms import ProfileForm

from .forms import RegisterForm
from django.http import HttpResponse


# =================== REGISTRATION / LOGIN / LOGOUT ===================

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.additional_info.ready_for_verification = True
            user.additional_info.save()
            messages.success(request, 'Регистрация прошла успешно! Письмо будет отправлено в течение минуты.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'base/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль.')
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
        return render(request, 'base/verification_success.html')
    else:
        return render(request, 'base/verification_failed.html')


@login_required
def request_verification_view(request):
    user = request.user
    user.additional_info.ready_for_verification = True
    user.additional_info.save()
    messages.success(request, "Письмо с подтверждением выслано вам на почту, пожалуйста подтвердите вашу учетную запись.")
    return redirect('home')

@login_required
def home_view(request):
    user = User.objects.select_related("additional_info").get(id=request.user.id)
    return render(request, 'base/home.html', {
        'user': user,
        'show_verification_notice': not user.additional_info.is_verified
    })


@login_required
def profile_edit_view(request):
    info = request.user.additional_info

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён!")
            return redirect('home')
    else:
        form = ProfileForm(instance=info)

    return render(request, 'base/profile_edit.html', {'form': form})

@login_required
def resend_verification_view(request):
    user = request.user
    if user.additional_info.is_verified:
        messages.info(request, "Вы уже подтверждены.")
    elif user.additional_info.ready_for_verification:
        messages.info(request, "Письмо уже в очереди на отправку.")
    else:
        user.additional_info.ready_for_verification = True
        user.additional_info.save()
        messages.success(request, "Письмо будет повторно отправлено в течение минуты.")
    return redirect('home')

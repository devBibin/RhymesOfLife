from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User

from .forms import RegisterForm
from .utils import generate_verification_link
from .notifications import ReportNotificator

from django.http import HttpResponse


# =================== REGISTRATION / LOGIN / LOGOUT ===================

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.additional_info.ready_for_verification = True
            user.additional_info.save()
            messages.success(request, 'Регистрация прошла успешно! Проверьте почту для подтверждения.')
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
    return render(request, 'base/home.html')


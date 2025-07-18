from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import AdditionalUserInfo

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            AdditionalUserInfo.objects.create(
                user=user,
                email=user.email,
                ready_for_verification=True
            )

        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = AdditionalUserInfo
        fields = ['avatar','first_name', 'last_name', 'syndrome', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'syndrome': forms.Textarea(attrs={'rows': 3}),
        }
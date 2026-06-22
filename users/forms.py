from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from urllib.parse import urlparse
import re

User = get_user_model()

PHONE_REGEX_8 = re.compile(r'^8\d{10}$')
PHONE_REGEX_PLUS7 = re.compile(r'^\+7\d{10}$')


def normalize_phone(value: str) -> str:
    value = value.strip()
    if PHONE_REGEX_8.match(value):
        # convert 8XXXXXXXXXX to +7XXXXXXXXXX
        return "+7" + value[1:]
    elif PHONE_REGEX_PLUS7.match(value):
        return value
    return value


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label="Подтвердите пароль"
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # Логин = Email
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "about", "phone", "github_url", "avatar")
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Телефон обязателен')
        normalized = normalize_phone(phone)
        if not (PHONE_REGEX_PLUS7.match(normalized)):
            raise ValidationError('Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX')

        # ensure unique phone (exclude current user)
        qs = User.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Пользователь с таким телефоном уже существует')
        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url', '').strip()
        if not url:
            return url
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError('Неверный URL')
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            raise ValidationError('Ссылка должна вести на github.com')
        return url

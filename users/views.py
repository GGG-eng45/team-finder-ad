import json
from http import HTTPStatus

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator

from .forms import RegistrationForm, LoginForm, ProfileEditForm
from .models import Skill, UserSkill

User = get_user_model()
SKILLS_AMOUNT = 10


def get_page_object(queryset, request, per_page=12):
    """Вспомогательная функция для пагинации"""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, "users/user_details.html", {"user": user})


def user_list(request):
    skill_name = request.GET.get('skill', '').strip()
    participants_qs = User.objects.all().order_by('id')

    if skill_name:
        participants_qs = participants_qs.filter(
            skills__name__iexact=skill_name
        ).distinct()

    page_obj = get_page_object(participants_qs, request)

    context = {
        'participants': page_obj,
        'all_skills': Skill.objects.all().order_by('name'),
        'active_skill': skill_name,
    }
    return render(request, 'users/participants.html', context)


@require_http_methods(["GET"])
def search_skills(request):
    """Autocomplete endpoint for skills.

    Returns a JSON list of up to 10 skills that start with the query (case-insensitive),
    ordered alphabetically.
    Format: [ {"id": <id>, "name": "<name>"}, ... ]
    """
    query = request.GET.get("q", "").strip()
    if len(query) < 1:
        return JsonResponse([], safe=False)

    skills = Skill.objects.filter(name__istartswith=query).order_by('name')[:SKILLS_AMOUNT]
    data = list(skills.values("id", "name"))
    return JsonResponse(data, safe=False)


@require_http_methods(["POST"])
@login_required
def add_skill(request, user_id):
    """Add a skill to a user (owner only).

    Accepts either form-encoded data or JSON with either skill_id or name.
    Returns JSON: {"skill_id": <id>, "created": <bool>, "added": <bool>}
    """
    if request.user.id != user_id:
        return JsonResponse({"error": "Нельзя добавить навык другому пользователю"}, status=HTTPStatus.FORBIDDEN)

    # Support JSON body or form data
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат данных"}, status=HTTPStatus.BAD_REQUEST)
        skill_id = payload.get('skill_id')
        name = payload.get('name', '').strip()
    else:
        skill_id = request.POST.get('skill_id')
        name = request.POST.get('name', '').strip()

    created = False
    added = False

    if skill_id:
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return JsonResponse({"error": "Навык не найден"}, status=HTTPStatus.BAD_REQUEST)
    elif name:
        # try to find case-insensitively first
        skill = Skill.objects.filter(name__iexact=name).first()
        if not skill:
            skill = Skill.objects.create(name=name)
            created = True
    else:
        return JsonResponse({"error": "skill_id или name обязателен"}, status=HTTPStatus.BAD_REQUEST)

    # link to user via UserSkill if not already
    user_skill, was_created = UserSkill.objects.get_or_create(user=request.user, skill=skill)
    if was_created:
        added = True

    return JsonResponse({"skill_id": skill.id, "created": created, "added": added})


@require_http_methods(["POST"])
@login_required
def remove_skill(request, user_id, skill_id):
    """Remove a skill from a user (owner only).

    Endpoint: POST /users/<user_id>/skills/<skill_id>/remove/
    Returns: {"removed": true}
    """
    if request.user.id != user_id:
        return JsonResponse({"error": "Нельзя удалить навык другого пользователя"}, status=HTTPStatus.FORBIDDEN)

    skill = get_object_or_404(Skill, id=skill_id)
    user_skill = UserSkill.objects.filter(user=request.user, skill=skill).first()
    if not user_skill:
        return JsonResponse({"error": "Навык не привязан к пользователю"}, status=HTTPStatus.BAD_REQUEST)

    user_skill.delete()
    return JsonResponse({"removed": True})


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # auto-login
            authenticated = authenticate(username=user.username, password=form.cleaned_data["password"])
            if authenticated:
                login(request, authenticated)
                return redirect("projects:project_list")
            return redirect("login")
        else:
            return render(request, "users/register.html", {"form": form, "error": "Проверьте правильность заполнения полей"})
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                user = User.objects.get(email=email)
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user:
                    login(request, authenticated_user)
                    return redirect("projects:project_list")
                return render(request, "users/login.html", {"form": form, "error": "Неверный email или пароль"})
            except User.DoesNotExist:
                return render(request, "users/login.html", {"form": form, "error": "Неверный email или пароль"})
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:project_list")


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:profile", user_id=request.user.id)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Пароль успешно изменён")
            return redirect("users:profile", user_id=request.user.id)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})

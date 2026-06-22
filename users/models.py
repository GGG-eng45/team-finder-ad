from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(
        "Аватар", upload_to="users/avatars/", blank=True, null=True
    )

    name = models.CharField("Имя", max_length=124, blank=False, default="")
    surname = models.CharField("Фамилия", max_length=124, blank=False, default="")
    about = models.TextField("О себе", blank=True, default="")
    phone = models.CharField("Телефон", max_length=12, blank=False, default="")
    github_url = models.URLField("GitHub", blank=True, default="")

    # Оставляем стандартные поля, но переопределяем related_name, чтобы не было ошибок
    groups = models.ManyToManyField(
        "auth.Group", related_name="custom_user_set", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="custom_user_permission_set", blank=True
    )

    # Навыки: ManyToMany через промежуточную модель UserSkill
    # определена ниже
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname}"


class Skill(models.Model):
    """Навык (уникальное название)"""

    name = models.CharField("Название навыка", max_length=124, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Связь пользователь ↔ навык"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_skills")
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="users_with_skill"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "skill"], name="unique_user_skill")
        ]
        ordering = ["-created_at"]
        verbose_name = "Навык пользователя"
        verbose_name_plural = "Навыки пользователей"

    def __str__(self):
        return f"{self.user} — {self.skill}"

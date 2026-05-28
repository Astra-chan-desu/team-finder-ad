from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    STATUS_CHOICES = [
        ("open", "Открытый"),
        ("closed", "Закрытый"),
    ]

    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    status = models.CharField(
        "Статус", max_length=10, choices=STATUS_CHOICES, default="open"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",  # чтобы шаблон мог user.owned_projects.all
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="participants",  # project.participants.all
    )
    github_url = models.URLField("GitHub проекта", blank=True)
    created_at = models.DateTimeField("Дата публикации", default=timezone.now)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "project")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"

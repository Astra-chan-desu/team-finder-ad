from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, Favorite

User = get_user_model()


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="author@b.com", password="123")
        self.project = Project.objects.create(
            name="Тестовый проект",
            description="Описание",
            owner=self.user,
            status="open",
        )

    def test_project_creation(self):
        self.assertEqual(str(self.project), "Тестовый проект")
        self.assertEqual(self.project.status, "open")
        self.assertTrue(Project.objects.exists())

    def test_owner_is_participant(self):
        # Не проверяем автоматическое добавление, т.к. это делается во view.
        # Просто проверим связь
        self.project.participants.add(self.user)
        self.assertIn(self.user, self.project.participants.all())


class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="dev@example.com", password="pass123", first_name="Dev"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="pass456"
        )
        self.project = Project.objects.create(
            name="Мой проект",
            description="Тестовое описание",
            owner=self.user,
            status="open",
        )
        self.project.participants.add(self.user)  # владелец уже участник

    def test_project_list_view(self):
        response = self.client.get(reverse("projects:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мой проект")

    def test_project_detail_view(self):
        url = reverse("projects:detail", kwargs={"pk": self.project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мой проект")
        self.assertContains(response, "Dev")

    def test_create_project_requires_login(self):
        response = self.client.get(reverse("projects:create_project"))
        self.assertRedirects(response, "/users/login/?next=/projects/create-project/")

    def test_create_project_success(self):
        self.client.login(email="dev@example.com", password="pass123")
        response = self.client.post(
            reverse("projects:create_project"),
            {
                "name": "Новый проект",
                "description": "Описание",
                "status": "open",
            },
        )
        self.assertEqual(response.status_code, 302)
        new_project = Project.objects.get(name="Новый проект")
        self.assertEqual(new_project.owner, self.user)
        self.assertIn(self.user, new_project.participants.all())

    def test_edit_project_owner(self):
        self.client.login(email="dev@example.com", password="pass123")
        url = reverse("projects:edit_project", kwargs={"pk": self.project.pk})
        response = self.client.post(
            url,
            {
                "name": "Измененный проект",
                "description": "Новое описание",
                "status": "open",
            },
        )
        self.assertRedirects(
            response, reverse("projects:detail", kwargs={"pk": self.project.pk})
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Измененный проект")

    def test_edit_project_not_owner(self):
        self.client.login(email="other@example.com", password="pass456")
        url = reverse("projects:edit_project", kwargs={"pk": self.project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_complete_project_owner(self):
        self.client.login(email="dev@example.com", password="pass123")
        url = reverse("projects:complete_project", kwargs={"pk": self.project.pk})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_complete_project_forbidden(self):
        self.client.login(email="other@example.com", password="pass456")
        url = reverse("projects:complete_project", kwargs={"pk": self.project.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_toggle_participate_join(self):
        self.client.login(email="other@example.com", password="pass456")
        url = reverse("projects:toggle_participate", kwargs={"pk": self.project.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "participant": True})
        self.assertIn(self.other_user, self.project.participants.all())

    def test_toggle_participate_leave(self):
        self.client.login(email="dev@example.com", password="pass123")
        url = reverse("projects:toggle_participate", kwargs={"pk": self.project.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "participant": False})
        self.assertNotIn(self.user, self.project.participants.all())

    def test_favorite_add(self):
        self.client.login(email="other@example.com", password="pass456")
        url = reverse("projects:favorite_add", kwargs={"pk": self.project.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Favorite.objects.filter(user=self.other_user, project=self.project).exists()
        )

    def test_favorite_remove(self):
        Favorite.objects.create(user=self.other_user, project=self.project)
        self.client.login(email="other@example.com", password="pass456")
        url = reverse("projects:favorite_remove", kwargs={"pk": self.project.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Favorite.objects.filter(user=self.other_user, project=self.project).exists()
        )

    def test_favorite_list(self):
        Favorite.objects.create(user=self.user, project=self.project)
        self.client.login(email="dev@example.com", password="pass123")
        url = reverse("projects:favorites")
        response = self.client.get(url)
        self.assertContains(response, "Мой проект")

    def test_guest_cannot_create_project(self):
        response = self.client.post(
            reverse("projects:create_project"),
            {
                "name": "Гостевой",
                "description": "...",
            },
        )
        self.assertEqual(response.status_code, 302)  # редирект на логин


class AdminPermissionsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="admin"
        )
        self.user = User.objects.create_user(email="user@example.com", password="123")
        self.project = Project.objects.create(
            name="Проект", description="...", owner=self.user
        )

    def test_admin_can_edit_any_project(self):
        self.client.login(email="admin@example.com", password="admin")
        url = reverse("projects:edit_project", kwargs={"pk": self.project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_complete_any_project(self):
        self.client.login(email="admin@example.com", password="admin")
        url = reverse("projects:complete_project", kwargs={"pk": self.project.pk})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

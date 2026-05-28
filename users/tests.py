from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Skill

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Иван",
            last_name="Иванов",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.name, "Иван")
        self.assertEqual(user.surname, "Иванов")
        self.assertEqual(str(user), "Иван Иванов")

    def test_email_unique(self):
        User.objects.create_user(email="a@b.com", password="123")
        with self.assertRaises(Exception):
            User.objects.create_user(email="a@b.com", password="123")


class SkillModelTest(TestCase):
    def test_create_skill(self):
        skill = Skill.objects.create(name="Python")
        self.assertEqual(str(skill), "Python")
        self.assertTrue(Skill.objects.filter(name="Python").exists())

    def test_skill_unique(self):
        Skill.objects.create(name="Python")
        with self.assertRaises(Exception):
            Skill.objects.create(name="Python")


class RegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("users:register")
        self.data = {
            "name": "Петр",
            "surname": "Петров",
            "email": "petr@example.com",
            "password": "Str0ngP@ssw0rd",
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, reverse("users:login"))
        user = User.objects.get(email="petr@example.com")
        self.assertEqual(user.first_name, "Петр")
        self.assertEqual(user.last_name, "Петров")

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(email="petr@example.com", password="123")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пользователь с таким email уже существует")


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="login@example.com", password="TestPass123"
        )
        self.login_url = reverse("users:login")
        self.logout_url = reverse("users:logout")
        self.profile_url = reverse("users:profile", kwargs={"pk": self.user.pk})

    def test_login_correct(self):
        response = self.client.post(
            self.login_url, {"email": "login@example.com", "password": "TestPass123"}
        )
        self.assertRedirects(response, "/")
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_wrong_credentials(self):
        response = self.client.post(
            self.login_url, {"email": "login@example.com", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный email или пароль")

    def test_logout(self):
        self.client.login(email="login@example.com", password="TestPass123")
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, "/")
        self.assertFalse("_auth_user_id" in self.client.session)


class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="pass123",
            first_name="Анна",
            last_name="Сидорова",
            about="Тестировщик",
            phone="+79991112233",
            github_url="https://github.com/anna",
        )
        self.skill = Skill.objects.create(name="Django")
        self.user.skills.add(self.skill)

    def test_profile_view(self):
        url = reverse("users:profile", kwargs={"pk": self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Анна Сидорова")
        self.assertContains(response, "Тестировщик")
        self.assertContains(response, "Django")

    def test_profile_edit_owner(self):
        self.client.login(email="profile@example.com", password="pass123")
        url = reverse("users:edit_profile", kwargs={"pk": self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "name": "Анна-Мария",
                "surname": "Сидорова",
                "about": "Senior tester",
                "phone": "+79991112233",
                "github_url": "https://github.com/anna",
            },
        )
        self.assertRedirects(
            response, reverse("users:profile", kwargs={"pk": self.user.pk})
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Анна-Мария")

    def test_profile_edit_forbidden(self):
        other = User.objects.create_user(email="other@example.com", password="123")
        self.client.login(email="profile@example.com", password="pass123")
        url = reverse("users:edit_profile", kwargs={"pk": other.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class SkillAJAXTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="skills@example.com", password="pass123"
        )
        self.skill_python = Skill.objects.create(name="Python")
        self.skill_js = Skill.objects.create(name="JavaScript")
        self.add_url = reverse("users:skill_add", kwargs={"pk": self.user.pk})
        self.search_url = reverse("users:skills_search")

    def test_skill_search(self):
        response = self.client.get(self.search_url, {"q": "Py"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Python")

    def test_add_existing_skill(self):
        self.client.login(email="skills@example.com", password="pass123")
        response = self.client.post(
            self.add_url, data={"name": "Python"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"status": "ok", "id": self.skill_python.pk, "name": "Python"},
        )
        self.assertTrue(self.user.skills.filter(pk=self.skill_python.pk).exists())

    def test_add_new_skill(self):
        self.client.login(email="skills@example.com", password="pass123")
        response = self.client.post(
            self.add_url, data={"name": "Docker"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.skills.filter(name="Docker").exists())
        self.assertTrue(Skill.objects.filter(name="Docker").exists())

    def test_add_skill_unauthorized(self):
        response = self.client.post(self.add_url, data={"name": "Python"})
        self.assertEqual(response.status_code, 302)  # login redirect

    def test_remove_skill(self):
        self.user.skills.add(self.skill_js)
        self.client.login(email="skills@example.com", password="pass123")
        remove_url = reverse(
            "users:skill_remove",
            kwargs={"pk": self.user.pk, "skill_id": self.skill_js.pk},
        )
        response = self.client.post(remove_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.assertFalse(self.user.skills.filter(pk=self.skill_js.pk).exists())


class UserListFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="alice@example.com",
            password="123",
            first_name="Алиса",
            last_name="Иванова",
        )
        self.user2 = User.objects.create_user(
            email="boris@example.com",
            password="123",
            first_name="Борис",
            last_name="Петров",
        )
        self.skill_py = Skill.objects.create(name="Python")
        self.skill_java = Skill.objects.create(name="Java")
        self.user1.skills.add(self.skill_py)
        self.user2.skills.add(self.skill_java)
        self.list_url = reverse("users:list")

    def test_list_all_users(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Алиса")
        self.assertContains(response, "Борис")

    def test_filter_by_skill(self):
        response = self.client.get(self.list_url, {"skill": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["page_obj"], [self.user1])

    def test_filter_reset(self):
        response = self.client.get(self.list_url, {"skill": "Nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["page_obj"], [])

    def test_filter_panel_contains_all_skills(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, "Python")
        self.assertContains(response, "Java")

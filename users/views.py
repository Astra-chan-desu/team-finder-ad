from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.views.generic import DetailView, ListView
from django.shortcuts import get_object_or_404
from .models import User, Skill
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import Skill
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .forms import UserProfileForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.views import PasswordChangeView as AuthPasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


class LogoutView(BaseLogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class EditProfileRedirectView(View):
    def get(self, request):
        return redirect("users:edit_profile", pk=request.user.pk)


class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class UserDetailView(DetailView):
    model = User
    template_name = "users/user-details.html"
    context_object_name = "user"
    pk_url_kwarg = "pk"


class UserListView(ListView):
    model = User
    template_name = "users/participants.html"
    paginate_by = 12
    ordering = ["-date_joined"]

    def get_queryset(self):
        queryset = super().get_queryset()
        skill_filter = self.request.GET.get("skill", "").strip()
        if skill_filter:
            queryset = queryset.filter(skills__name=skill_filter).distinct()
            self.active_skill = skill_filter
        else:
            self.active_skill = None
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_skills"] = Skill.objects.all()
        if self.active_skill:
            try:
                skill_obj = Skill.objects.get(name=self.active_skill)
            except Skill.DoesNotExist:
                skill_obj = None
            context["active_skill"] = skill_obj
        else:
            context["active_skill"] = None
        return context


class SkillSearchView(View):
    """Автодополнение навыков (GET /users/skills/?q=...)"""

    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse([], safe=False)
        # Ищем навыки, начинающиеся с query (до 10)
        skills = Skill.objects.filter(name__istartswith=query).values_list(
            "id", "name"
        )[:10]
        return JsonResponse([{"id": s[0], "name": s[1]} for s in skills], safe=False)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_required, name="dispatch")
class SkillAddView(View):
    def post(self, request, pk):
        if request.user.pk != pk:
            return JsonResponse({"error": "Нет прав"}, status=403)

        user = request.user
        data = json.loads(request.body)
        skill_id = data.get("skill_id")
        name = data.get("name")

        if skill_id:
            skill = get_object_or_404(Skill, pk=skill_id)
        elif name:
            skill, created = Skill.objects.get_or_create(name=name.strip())
        else:
            return JsonResponse({"error": "Не указан навык"}, status=400)

        if user.skills.filter(pk=skill.pk).exists():
            return JsonResponse(
                {"status": "already_added", "id": skill.pk, "name": skill.name}
            )

        user.skills.add(skill)
        return JsonResponse({"status": "ok", "id": skill.pk, "name": skill.name})


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_required, name="dispatch")
class SkillRemoveView(View):
    """Удаление навыка у пользователя (POST)"""

    def post(self, request, pk, skill_id):
        if request.user.pk != pk:
            return JsonResponse({"error": "Нет прав"}, status=403)

        user = request.user
        skill = get_object_or_404(Skill, pk=skill_id)
        user.skills.remove(skill)
        return JsonResponse({"status": "ok"})


class UserEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "users/edit_profile.html"

    def test_func(self):
        return self.request.user.pk == self.kwargs.get("pk")

    def get_success_url(self):
        return reverse_lazy("users:profile", kwargs={"pk": self.object.pk})


class PasswordChangeView(AuthPasswordChangeView):
    template_name = "users/change_password.html"

    def get_success_url(self):
        return reverse_lazy("users:profile", kwargs={"pk": self.request.user.pk})


def logout_view(request):
    auth_logout(request)
    return redirect("/")

import json
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required      
 
from django.utils.decorators import method_decorator
from django.urls import reverse

from .models import Project, Favorite
from .forms import ProjectForm


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['favorite_project_ids'] = list(
                Favorite.objects.filter(user=self.request.user)
                .values_list('project_id', flat=True)
            )
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project-details.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user
        if user.is_authenticated:
            context['is_participant'] = project.participants.filter(pk=user.pk).exists()
            context['is_favorite'] = Favorite.objects.filter(
                user=user, project=project
            ).exists()
        else:
            context['is_participant'] = False
            context['is_favorite'] = False
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        self.object = form.save()
        self.object.participants.add(self.request.user)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.owner or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.object.pk})


class ProjectCompleteView(LoginRequiredMixin, View):
    """Завершить проект (статус 'closed')"""
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if request.user != project.owner and not request.user.is_staff:
            return HttpResponseForbidden()
        project.status = 'closed'
        project.save()
        return JsonResponse({
            'status': 'ok',
            'reload': True,
            'redirect_url': reverse('projects:detail', kwargs={'pk': pk})
        })

    def get(self, request, pk):
        return self.post(request, pk)
    
    
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class ToggleParticipateView(View):
    """Присоединиться / выйти из проекта (AJAX)"""
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user
        if project.participants.filter(pk=user.pk).exists():
            project.participants.remove(user)
            participant = False
        else:
            project.participants.add(user)
            participant = True
        return JsonResponse({'status': 'ok', 'participant': participant})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class FavoriteAddView(View):
    """Добавить проект в избранное (AJAX)"""
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        _, created = Favorite.objects.get_or_create(user=request.user, project=project)
        return JsonResponse({'status': 'ok', 'action': 'added' if created else 'already_exists'})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class FavoriteRemoveView(View):
    """Удалить проект из избранного (AJAX)"""
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        Favorite.objects.filter(user=request.user, project=project).delete()
        return JsonResponse({'status': 'ok', 'action': 'removed'})


class FavoriteListView(LoginRequiredMixin, ListView):
    template_name = 'projects/favorite_projects.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        return Project.objects.filter(
            favorited_by__user=self.request.user
        ).order_by('-created_at')
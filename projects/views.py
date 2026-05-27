from django.views.generic import ListView
from .models import Project

class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    ordering = ['-created_at']
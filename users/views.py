from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm

class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'  
    success_url = reverse_lazy('login')
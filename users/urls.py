from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (UserRegisterView, UserDetailView, UserListView,
                    SkillSearchView, SkillAddView, SkillRemoveView,
                    UserEditView, EditProfileRedirectView, PasswordChangeView)
from .forms import EmailAuthenticationForm
from django.urls import reverse_lazy
app_name = 'users'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html',
        redirect_authenticated_user=True,
        authentication_form=EmailAuthenticationForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('skills/', SkillSearchView.as_view(), name='skills_search'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
    template_name='users/change_password.html',
    success_url=reverse_lazy('users:profile'),  
), name='change_password'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('list/', UserListView.as_view(), name='list'),  
    path('edit-profile/', EditProfileRedirectView.as_view(), name='edit_profile_redirect'),

    path('<int:pk>/', UserDetailView.as_view(), name='profile'),
    path('<int:pk>/edit/', UserEditView.as_view(), name='edit_profile'),
    path('<int:pk>/skills/add/', SkillAddView.as_view(), name='skill_add'),
    path('<int:pk>/skills/<int:skill_id>/remove/', SkillRemoveView.as_view(), name='skill_remove'),
]
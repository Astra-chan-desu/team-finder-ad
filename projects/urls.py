from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='home'),
    path('create-project/', views.ProjectCreateView.as_view(), name='create_project'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='edit_project'),
    path('<int:pk>/complete/', views.ProjectCompleteView.as_view(), name='complete_project'),
    path('<int:pk>/toggle-participate/', views.ToggleParticipateView.as_view(), name='toggle_participate'),
    path('<int:pk>/favorite/add/', views.FavoriteAddView.as_view(), name='favorite_add'),
    path('<int:pk>/favorite/remove/', views.FavoriteRemoveView.as_view(), name='favorite_remove'),
    path('favorites/', views.FavoriteListView.as_view(), name='favorites'),
    path('list/', RedirectView.as_view(pattern_name='projects:home', permanent=False)),
]
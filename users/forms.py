from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=30, required=True, label='Имя')
    surname = forms.CharField(max_length=30, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('name', 'surname', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['name']
        user.last_name = self.cleaned_data['surname']
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']   
        if commit:
            user.save()
        return user
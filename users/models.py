from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    about = models.TextField('О себе', blank=True, max_length=500)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    github_url = models.URLField('GitHub', blank=True)

    skills = models.ManyToManyField('Skill', blank=True, related_name='users', verbose_name='Навыки')

    @property
    def name(self):
        return self.first_name

    @name.setter
    def name(self, value):
        self.first_name = value

    @property
    def surname(self):
        return self.last_name

    @surname.setter
    def surname(self, value):
        self.last_name = value

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Skill(models.Model):
    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ['name']

    def __str__(self):
        return self.name
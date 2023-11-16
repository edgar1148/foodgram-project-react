from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Кастомная модель пользователя"""
    username = models.CharField(max_length=150, unique=True,
                                verbose_name='Логин')
    first_name = models.CharField(max_length=150, blank=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=False,
                                 verbose_name='Фамилия')
    email = models.EmailField(max_length=254, blank=False, unique=True,
                              verbose_name='email')
    password = models.CharField(max_length=150, blank=False,
                                verbose_name='Пароль')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.get_full_name()

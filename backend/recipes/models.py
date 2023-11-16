from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(max_length=200,
                            blank=False,
                            verbose_name='Название')

    measurement_unit = models.CharField(max_length=200,
                                        blank=False,
                                        verbose_name='Единица измерения')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тэгов"""
    name = models.CharField(max_length=200,
                            blank=False,
                            unique=True,
                            verbose_name='Название тэга')

    color = models.CharField(max_length=7,
                             blank=False,
                             default='#ffffff',
                             verbose_name='Цвет тэга')

    slug = models.SlugField(unique=True,
                            blank=False,
                            verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               blank=False,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(max_length=200,
                            blank=False,
                            verbose_name='Название')
    text = models.TextField(blank=False,
                            verbose_name='Описание')
    image = models.ImageField(upload_to='media/',
                              blank=False,
                              verbose_name='Картинка')
    ingredients = models.ManyToManyField(Ingredient,
                                         blank=False,
                                         related_name='recipes',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag,
                                  blank=False,
                                  related_name='recipes',
                                  verbose_name='Тэги')
    cooking_time = models.PositiveSmallIntegerField(
        blank=False,
        verbose_name='Время готовки')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Products(models.Model):
    """Модель промежуточная"""
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_ingredients',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='ingredient_recipes',
                                   verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(blank=False,
                                              verbose_name='Количество')

    class Meta:
        verbose_name = 'Продукт',
        verbose_name_plural = 'Продукты'


class Follow(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Подписываемый')

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'


class Favorites(models.Model):
    """Модель избранного"""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='user_favorites',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               null=True,
                               related_name='favorites',
                               verbose_name='Рецепты')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Списки избранного'

    def __str__(self):
        return f'Избранное {self.user}'


class ShoppingList(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='shopping_list',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               null=True,
                               related_name='shopping_list',
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок {self.user}'

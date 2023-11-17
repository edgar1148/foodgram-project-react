from django.contrib.auth import get_user_model
from django_filters.rest_framework import filters

from recipes.models import Ingredient, Recipe

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтрация рецептов"""
    author = filters.ModelChoiceFilter(field_name='author',
                                       queryset=User.objects.all(),)
    is_favorited = filters.BooleanFilter(method='get_favorite')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_favorite(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset


class NameIngredientsFilter(filters.FilterSet):
    """Фильтрация ингредиентов"""
    name = filters.CharFilter(field_name='name')

    class Meta:
        model = Ingredient
        fields = ('name',)

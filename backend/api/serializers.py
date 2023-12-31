from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.core.exceptions import ValidationError

from users.models import User
from recipes.models import (Ingredient, Tag, Recipe,
                            Products, Favorites, Follow, ShoppingList)
from api.constants import MIN_VAL, MAX_VAL


class OutputUsersSerializer(UserSerializer):
    """Вывод пользователей"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        user = request.user
        if user.is_authenticated:
            return user.follower.filter(author=obj).exists()
        return False


class UserCreateSerializer(UserCreateSerializer):
    """Создание пользователя"""

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок"""
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'is_subscribed',
                  'recipes_count', 'recipes',)

    def get_recipes(self, obj):
        request = self.context['request'].user
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_attribute(self, obj):
        return obj.author.recipes.all()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = self.context['request'].user
        if not request or not user.is_authenticated:
            return False
        return obj.following.filter(user=user).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.Serializer):
    """Управление подписками"""

    def validate(self, data):
        user = self.context['request'].user
        author = get_object_or_404(User, pk=self.context['id'])
        if user == author:
            raise serializers.ValidationError()
        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError()
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        author = get_object_or_404(User, pk=validated_data['id'])
        Follow.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': self.context.get('request')})
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткий вывод рецептов"""
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля"""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)


class ProductsGetSerializer(serializers.ModelSerializer):
    """Получение продуктов из рецепта"""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = Products
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    """Список рецептов"""
    author = OutputUsersSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault())
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ProductsGetSerializer(
        many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time',)

    def get_ingredients(self, obj):
        queryset = obj.recipe_ingredients.filter(recipe=obj)
        return ProductsGetSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.user_favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.shopping_list.filter(recipe=obj).exists()


class AddIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингредиентов"""
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField(min_value=MIN_VAL,
                                      max_value=MAX_VAL)

    class Meta:
        model = Products
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Операции с рецептами"""
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = AddIngredientsSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    cooking_time = serializers.IntegerField(min_value=MIN_VAL,
                                            max_value=MAX_VAL)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time', 'author',)

    def validate_tags(self, data):
        tags = data
        if not tags:
            raise ValidationError('Выбериет тэг')
        tags_list = set([])
        for tag in tags:
            if tag in tags_list:
                raise ValidationError('Такой тэг есть')
            tags_list.add(tag)
        return data

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError('Отсутствуют ингридиенты')
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = set([])
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError('Одинаковые ингредиенты')
            ingredients_list.add(ingredient_id)
        return data

    def add_ingredients(self, recipe, data):
        if not data:
            raise serializers.ValidationError('Ошибка')
        ingredients = []
        for ingredient_data in data:
            ingredient_id = ingredient_data['ingredient']['id']
            if ingredient_id in ingredients:
                raise serializers.ValidationError('Одинаковые ингредиенты')
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            if recipe.recipe_ingredients.filter(
                    ingredient=ingredient_id).exists():
                amount += F('amount')
            recipe_ingredient = Products(recipe=recipe, ingredient=ingredient,
                                         amount=amount)
            ingredients.append(recipe_ingredient)
        Products.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags')
        Products.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)
        instance.tags.set(tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeGetSerializer(instance, context=context).data


class FavoritesSerializer(serializers.Serializer):
    """Сериализатор избранного"""

    def validate(self, data):
        recipe_id = self.context['recipe_id']
        user = self.context['request'].user
        if user.favorites.filter(recipe_id=recipe_id).exists():
            raise serializers.ValidationError('error')
        return data

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, pk=validated_data['id'])
        user = self.context['request'].user
        Favorites.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return serializer.data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}).data


class ShoppingListSerializer(serializers.Serializer):
    """Управление списком покупок"""

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def validate(self, data):
        recipe_id = self.context['recipe_id']
        user = self.context['request'].user
        if user.shopping_list.filter(recipe_id=recipe_id).exists():
            raise serializers.ValidationError('Ошибка')
        return data

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, pk=validated_data['id'])
        ShoppingList.objects.create(
            user=self.context['request'].user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return serializer.data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}).data

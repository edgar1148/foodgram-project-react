from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

from recipes.models import (Ingredient, Tag, Recipe, Products, Favorites,
                            ShoppingList,)
from api.serializers import (FavoritesSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeGetSerializer,
                             ChangePasswordSerializer, ShoppingListSerializer,
                             SubscribeSerializer, SubscriptionSerializer,
                             TagSerializer, UserCreateSerializer,
                             OutputUsersSerializer, ShortRecipeSerializer)
from api.pagination import Paginator
from api.filters import NameIngredientsFilter, RecipeFilter


User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингридиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NameIngredientsFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тэгов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = Paginator
    http_method_names = ['get', 'post', 'patch', 'delete', ]
    serializer_action_classes = {
        'list': RecipeGetSerializer,
        'retrieve': RecipeGetSerializer,
        'favorite': FavoritesSerializer,
        'shopping_cart': ShoppingListSerializer,
    }

    def get_serializer_class(self):
        """Выбор сериализатора"""
        try:
            return self.serializer_action_classes[self.action]
        except Exception:
            return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=('post', 'delete',), detail=True,
            serializer_class=FavoritesSerializer,
            permission_classes=(IsAuthenticated,),)
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            serializer = ShortRecipeSerializer(recipe, data=request.data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            if not recipe.favorites.filter(user=request.user).exists():
                Favorites.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            get_object_or_404(Favorites, user=request.user,
                              recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('post', 'delete',),
            detail=True,
            serializer_class=ShoppingListSerializer,
            permission_classes=(IsAuthenticated,),)
    def shopping_cart(self, request, pk=None):

        if self.request.method == 'POST':
            return self.add_recipe_to_cart(request, pk)
        if self.request.method == 'DELETE':
            return self.delete_recipe_from_cart(request, pk)

    def add_recipe_to_cart(self, request, pk):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'recipe_id': pk})
        serializer.is_valid(raise_exception=True)
        response_data = serializer.save(id=pk)
        return Response({'data': response_data},
                        status=status.HTTP_201_CREATED)

    def delete_recipe_from_cart(self, request, pk):

        get_object_or_404(ShoppingList, user=self.request.user,
                          recipe=get_object_or_404(Recipe, pk=pk)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,),)
    def download_shopping_cart(self, request):
        shopping_cart = request.user.shopping_list.filter(
            user=self.request.user)
        current_list = shopping_list_info(shopping_cart)
        response = HttpResponse(current_list, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt')
        return response


def shopping_list_info(shopping_list):
    recipes = shopping_list.values_list('recipe_id', flat=True)
    shop_list = Products.objects.filter(
        recipe__in=recipes).values('ingredient').annotate(
            amount=Sum('amount'))
    current_list = 'Список покупок'
    for unit in shop_list:
        ingredient = Ingredient.objects.get(pk=unit['ingredient'])
        amount = unit['amount']
        current_list += (
            f'{ingredient.name}, {amount}, {ingredient.measurement_unit}')
    return current_list


class UserViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                  mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Вьюсет работы с пользователем"""
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('username',)
    filterset_fields = ('username',)
    permission_classes = (AllowAny,)
    serializer_action_classes = {
        'list': OutputUsersSerializer,
        'retrieve': OutputUsersSerializer,
        'set_password': ChangePasswordSerializer,
        'subscribe': SubscribeSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except Exception:
            return UserCreateSerializer

    @action(methods=('get',), detail=False,
            permission_classes=(IsAuthenticated,),)
    def me(self, request):
        serializer = OutputUsersSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=False,
            serializer_class=ChangePasswordSerializer,
            permission_classes=(IsAuthenticated,),)
    def set_password(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')
        if not user.check_password(old_password):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post', 'delete'),
            serializer_class=SubscribeSerializer,
            permission_classes=(IsAuthenticated,),)
    def subscribe(self, request, pk=None):
        if request.method == 'POST':
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request, 'id': pk})
            serializer.is_valid(raise_exception=True)
            response_data = serializer.save(id=pk)
            return Response({'properties': response_data},
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            user = self.request.user
            subscription = user.follower.filter(
                author=get_object_or_404(User, pk=pk))
            if not subscription.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=False,
            serializer_class=SubscriptionSerializer,
            permission_classes=(IsAuthenticated,),
            pagination_class=Paginator)
    def subscriptions(self, request):
        user = request.user
        follow_list = user.following.all()
        paginated_queryset = self.paginate_queryset(follow_list)
        serializer = self.serializer_class(paginated_queryset,
                                           context={'request': request},
                                           many=True)
        return self.get_paginated_response(serializer.data)

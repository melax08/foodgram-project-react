from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.permissions import IsAuthorOrAdminOrReadOnly
from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Tag)
from users.models import Follow, User

from .constants import (SHOPPING_CART_FILENAME, SHOPPING_CART_FOOTER,
                        SHOPPING_CART_HEADER)
from .filters import RecipeFilter
from .serializers import (CreateRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortInfoSerializer,
                          TagSerializer, UserCreateSerializer,
                          UserGetRetrieveSerializer, UserSubscribeSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet for Tag model, only GET requests."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet for Ingredient model, only GET requests."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """ViewSet for Recipe model with extra actions."""
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = Recipe.objects.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe__pk=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    Cart.objects.filter(
                        user=self.request.user,
                        recipe__pk=OuterRef('pk')
                    )
                )
            )
        else:
            queryset = Recipe.objects.all()
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer
        if self.action in ('shopping_cart', 'favorite'):
            return RecipeShortInfoSerializer
        return self.serializer_class

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)

    def _recipe_processing(self, request, model, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite_object = model.objects.filter(user=request.user,
                                               recipe=recipe)
        if request.method == 'POST':
            if favorite_object.exists():
                raise serializers.ValidationError(
                    {
                        'errors': 'Рецепт уже добавлен.'
                    }
                )
            model.objects.create(user=request.user, recipe=recipe)
            return Response(self.get_serializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        if not favorite_object.exists():
            raise serializers.ValidationError(
                {
                    'errors': "Данный рецепт не добавлен."
                }
            )
        favorite_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, *args, **kwargs):
        return self._recipe_processing(request, Favorite, kwargs['pk'])

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, *args, **kwargs):
        return self._recipe_processing(request, Cart, kwargs['pk'])

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients_for_recipes = IngredientRecipe.objects.select_related(
            'ingredient', 'recipe')
        user_cart = ingredients_for_recipes.filter(
            recipe__in_cart__user=request.user)
        user_cart_ingredients = user_cart.values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(total=Sum('amount'))

        text = [SHOPPING_CART_HEADER]
        text.extend([f'{ingredient["ingredient__name"]}'
                     f' - {ingredient["total"]} '
                     f'{ingredient["ingredient__measurement_unit"]}'
                     for ingredient in user_cart_ingredients])
        text.append(f'\n{SHOPPING_CART_FOOTER}')
        text = '\n'.join(text)

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={SHOPPING_CART_FILENAME}')
        return response


class CustomUserViewSet(UserViewSet):
    """Extended djoser user viewset with extra actions
    (subscribe and subscriptions).
    """
    queryset = User.objects.all()
    serializer_class = UserGetRetrieveSerializer
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action in ('subscriptions', 'subscribe'):
            return UserSubscribeSerializer
        if self.action == 'create':
            return UserCreateSerializer
        return super().get_serializer_class()

    @action(detail=False)
    def subscriptions(self, request):
        following = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(following, many=True)
                        .data)  # pragma: no cover

    @action(detail=True, methods=['post', 'delete'],
            http_method_names=['post', 'delete'])
    def subscribe(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs['id'])
        follow_object = Follow.objects.filter(user=request.user, author=author)
        if request.method == 'POST':
            if request.user == author:
                raise serializers.ValidationError(
                    {'errors': 'Вы не можете подписываться на самого себя!'})
            if follow_object.exists():
                raise serializers.ValidationError(
                    {'errors': 'Вы уже подписаны на этого пользователя.'})
            Follow.objects.create(user=request.user, author=author)
            return Response(self.get_serializer(author).data,
                            status=status.HTTP_201_CREATED)

        if not follow_object.exists():
            raise serializers.ValidationError(
                {'errors': 'Вы не подписаны на этого автора.'})
        follow_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

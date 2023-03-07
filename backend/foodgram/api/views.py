from django.http import HttpResponse
from django.db.models import Sum, F
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import permissions, serializers, status
from django.shortcuts import get_object_or_404

from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeSerializer, CreateRecipeSerializer)
from recipes.models import Tag, Ingredient, Recipe, Favorite, Cart, IngredientRecipe
from core.serializers import RecipeShortInfoSerializer

SHOPPING_CART_HEADER = 'Ваш список покупок:'
SHOPPING_CART_FOOTER = 'Foodgram - лучший сайт с рецептами.'
SHOPPING_CART_FILENAME = 'foodgram_shopping_list.txt'


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    # Тут кастомный пермишен с автором, безопасными методами и одменом

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return CreateRecipeSerializer
        return RecipeSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)

    @staticmethod
    def _recipe_processing(request, model, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite_object = model.objects.filter(user=request.user,
                                               recipe=recipe)
        if request.method == 'POST':
            if favorite_object.exists():
                raise serializers.ValidationError(
                    {'errors': 'Рецепт уже добавлен.'})
            model.objects.create(user=request.user, recipe=recipe)
            return Response(RecipeShortInfoSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        if not favorite_object.exists():
            raise serializers.ValidationError(
                {'errors': "Данный рецепт не добавлен."}
            )
        favorite_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        return self._recipe_processing(request, Favorite, kwargs['pk'])

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        return self._recipe_processing(request, Cart, kwargs['pk'])

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
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





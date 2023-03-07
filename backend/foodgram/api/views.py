from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import permissions, serializers, status
from django.shortcuts import get_object_or_404

from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeSerializer, CreateRecipeSerializer)
from recipes.models import Tag, Ingredient, Recipe, Favorite, Cart, IngredientRecipe
from core.serializers import RecipeShortInfoSerializer


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
        favorite_object = model.objects.filter(user=request.user, recipe=recipe)
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
        final_list = {}
        for cart_item in request.user.cart.all():
            cur_recipe = cart_item.recipe
            recipe_ings = cur_recipe.ingredients.all()
            for ing in recipe_ings:
                cur_ing = IngredientRecipe.objects.get(ingredient=ing,
                                                       recipe=cur_recipe)
                ingredient = cur_ing.ingredient.name
                measurement_unit = cur_ing.ingredient.measurement_unit
                amount = cur_ing.amount
                if final_list.get(ingredient) is not None:
                    final_list[ingredient][1] += amount
                else:
                    final_list[ingredient] = [measurement_unit, amount]
        text = '\n'.join(
            [f'{ingredient} - {misc[1]} {misc[0]}'
             for ingredient, misc in final_list.items()])
        file_name = 'foodgram_shopping_list.txt'
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response





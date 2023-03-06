from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework import permissions, serializers, status, mixins
from django.shortcuts import get_object_or_404

from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeSerializer, CreateRecipeSerializer)
from recipes.models import Tag, Ingredient, Recipe, Favorite
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

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['pk'])
        favorite_object = Favorite.objects.filter(user=request.user,
                                                  recipe=recipe)
        if request.method == 'POST':
            if favorite_object.exists():
                raise serializers.ValidationError(
                    {'errors': 'Рецепт уже есть в избраном.'})
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(RecipeShortInfoSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        if not favorite_object.exists():
            raise serializers.ValidationError(
                {'errors': "Данного рецепта нет в избранном."}
            )
        favorite_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





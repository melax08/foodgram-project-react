from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .serializers import (TagSerializer, IngredientSerializer, RecipeSerializer, CreateRecipeSerializer)
from recipes.models import Tag, Ingredient, Recipe


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

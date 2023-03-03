from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .serializers import (TagSerializer, IngredientSerializer, RecipeSerializer, CreateRecipeSerializer)
from recipes.models import Tag, Ingredient, Recipe


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRecipeSerializer
        return RecipeSerializer

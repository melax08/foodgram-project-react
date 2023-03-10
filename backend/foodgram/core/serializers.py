from rest_framework.serializers import ModelSerializer

from recipes.models import Recipe


class RecipeShortInfoSerializer(ModelSerializer):
    """Serializer for Recipe model with short information about recipe."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

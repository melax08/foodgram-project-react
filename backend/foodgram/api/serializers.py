import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.serializers import UserGetRetrieveSerializer


class Base64ImageField(serializers.ImageField):
    """Custom image field that allows to
    upload images as string encoded by base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr),
                               name=f'{get_random_string(length=20)}.{ext}')
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for represent IngredientRecipe model as nested field
    in GET requests."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for represent IngredientRecipe model as nested field
    in POST and PATCH requests."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Serializer for represent Recipe model in POST and PATCH requests."""
    author = UserGetRetrieveSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientRecipeCreateSerializer(many=True, write_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient,
                name=ingredient.get('ingredient').name
            )
            IngredientRecipe.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient.get('amount')
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        for key, data in validated_data.items():
            setattr(instance, key, data)
        instance.save()
        instance.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient,
                name=ingredient.get('ingredient').name
            )
            IngredientRecipe.objects.create(
                ingredient=current_ingredient,
                recipe=instance,
                amount=ingredient.get('amount')
            )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        data['ingredients'] = IngredientRecipeRetrieveSerializer(
            instance.recipe_ingredients.all(), many=True).data
        data['is_favorited'] = False
        data['is_in_shopping_cart'] = False
        return data


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for represent Recipe model in GET requests."""
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    author = UserGetRetrieveSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientRecipeRetrieveSerializer(
        many=True, source='recipe_ingredients')

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

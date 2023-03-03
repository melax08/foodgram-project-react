from django.shortcuts import get_object_or_404
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe, Favorite, Cart, TagRecipe, IngredientRecipe
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              required=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'author',
                  'tags',
                  'ingredients',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient, name=ingredient.get('id'))
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            recipe=recipe,
                                            amount=ingredient.get('amount'))
        return recipe


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def is_added(self, model, obj):
        return model.objects.filter(
            user__username=self.context['request'].user,
            recipe=obj.id).exists()

    def get_is_favorited(self, obj):
        return self.is_added(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.is_added(Cart, obj)

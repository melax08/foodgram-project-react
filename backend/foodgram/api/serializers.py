from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from core.fields import Base64ImageField
from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.models import Follow, User


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model with short information about recipe."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserGetRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for user model. Only GET requests."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user__username=self.context['request'].user,
            author__username=obj.username).exists()


class UserSubscribeSerializer(UserGetRetrieveSerializer):
    """Serializer for subscribe actions. Represent user with extra info like
    user recipes and count of user recipes."""
    def to_representation(self, instance):
        data = super().to_representation(instance)
        recipes = RecipeShortInfoSerializer(instance.recipes, many=True)
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        if recipes_limit is None:
            data['recipes'] = recipes.data
        elif not recipes_limit.isnumeric():
            raise serializers.ValidationError(
                {'recipes_limit': 'Параметр должен быть '
                                  'положительным целым числом.'})
        else:
            data['recipes'] = recipes.data[:int(recipes_limit)]
        data['recipes_count'] = instance.recipes.count()
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user model. Only POST requests."""
    password = serializers.CharField(max_length=150,
                                     validators=[validate_password],
                                     write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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

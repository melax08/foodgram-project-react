from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User, Follow
from core.serializers import RecipeShortInfoSerializer


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
        user = User.objects.create_user(**validated_data)
        return user

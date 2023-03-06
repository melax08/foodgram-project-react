from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Follow

from recipes.models import Recipe


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user__username=self.context['request'].user,
            author__username=obj.username).exists()


class UserSubscribedSerializer(UserSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['recipes'] = RecipeShortInfoSerializer(instance.recipes,
                                                    many=True).data
        data['recipes_count'] = instance.recipes.count()
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=150,
                                     validators=[validate_password])
    # Протестировать, что-то с паролем, невозможно получить токен.

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

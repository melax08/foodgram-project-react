from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Follow


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, max_length=150,
                                     validators=[validate_password])

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'password')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user__username=self.context['request'].user,
            author__username=obj.username).exists()

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

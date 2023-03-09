from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, serializers
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

from .models import User, Follow
from .serializers import (UserSerializer,
                          UserSubscribedSerializer,
                          UserCreateSerializer)


class CustomUserViewSet(UserViewSet):
    """Extended djoser user viewset with extra actions
    (subscribe and subscriptions).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'subscriptions' or self.action == 'subscribe':
            return UserSubscribedSerializer
        if self.action == 'create':
            return UserCreateSerializer
        return super().get_serializer_class()

    @action(detail=False)
    def subscriptions(self, request):
        following = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(following, many=True).data)

    @action(detail=True, methods=['post', 'delete'],
            http_method_names=['post', 'delete'])
    def subscribe(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs['id'])
        follow_object = Follow.objects.filter(user=request.user, author=author)
        if request.method == 'POST':
            if request.user == author:
                raise serializers.ValidationError(
                    {'errors': 'Вы не можете подписываться на самого себя!'})
            if follow_object.exists():
                raise serializers.ValidationError(
                    {'errors': 'Вы уже подписаны на этого пользователя.'})
            Follow.objects.create(user=request.user, author=author)
            return Response(self.get_serializer(author).data,
                            status=status.HTTP_201_CREATED)

        if not follow_object.exists():
            raise serializers.ValidationError(
                {'errors': 'Вы не подписаны на этого автора.'})
        follow_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

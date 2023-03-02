from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import permissions

from .models import User
from .serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        return Response(self.get_serializer(request.user).data)



from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]

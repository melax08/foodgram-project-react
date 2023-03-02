from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import TagViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
]
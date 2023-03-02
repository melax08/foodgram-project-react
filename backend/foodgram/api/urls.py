from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import TagViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
]
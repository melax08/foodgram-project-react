from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Custom FilterSet that allows filter Recipe views
    by tags, is_favorited, is_in_shopping_cart and author fields."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='is_favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter'
    )
    author = filters.ModelMultipleChoiceFilter(
        field_name='author',
        queryset=User.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def is_favorited_filter(self, queryset, _, value):
        if value:
            return queryset.filter(followers__user=self.request.user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, _, value):
        if value:
            return queryset.filter(in_cart__user=self.request.user)
        return queryset

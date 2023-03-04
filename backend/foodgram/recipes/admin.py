from django.contrib import admin

from .models import Tag, Recipe, Ingredient, Favorite, Cart, IngredientRecipe, TagRecipe

admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)

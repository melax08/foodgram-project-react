from django.contrib import admin

from .models import (Tag, Recipe, Ingredient, Favorite, Cart,
                     IngredientRecipe, TagRecipe)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('favorite_count',)

    @staticmethod
    def favorite_count(obj):
        return obj.followers.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)

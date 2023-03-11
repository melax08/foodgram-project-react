from django.contrib import admin

from .models import (Cart, Favorite, Ingredient, IngredientRecipe, Recipe, Tag,
                     TagRecipe)


class TagInlineAdmin(admin.TabularInline):
    """Custom InLine field for represent many to many tags field in recipe."""
    model = Recipe.tags.through


class IngredientInlineAdmin(admin.TabularInline):
    """Custom InLine field for represent many to many ingredient field
    in recipe."""
    model = Recipe.ingredients.through


class RecipeAdmin(admin.ModelAdmin):
    """Settings for recipe in admin panel."""
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('favorite_count',)
    inlines = [TagInlineAdmin, IngredientInlineAdmin]

    @staticmethod
    def favorite_count(obj):
        return obj.followers.count()


class IngredientAdmin(admin.ModelAdmin):
    """Settings for ingredient in admin panel."""
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)

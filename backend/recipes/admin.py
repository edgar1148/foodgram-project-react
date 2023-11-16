from django.contrib import admin
from recipes.models import (Ingredient, Tag, Recipe, Follow, Favorites, ShoppingList, Products)


class ProductsAdmin(admin.TabularInline):
    model = Products


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorites')
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags',)
    inlines = [ProductsAdmin]

    def in_favorites(self, obj):
        return obj.favorites.count()


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Follow)
admin.site.register(Favorites)
admin.site.register(ShoppingList)

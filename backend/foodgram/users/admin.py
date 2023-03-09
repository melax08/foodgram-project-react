from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

from .models import User, Follow


class CustomUserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'username')


# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     list_filter = ('email', 'username')


admin.site.register(User, CustomUserAdmin)
admin.site.register(Follow)

from django.contrib import admin

from .models import User, Log


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'is_deleted', 'create_time')


class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'content', 'create_time')


admin.site.register(User, UserAdmin)
admin.site.register(Log, LogAdmin)

from django.contrib import admin

# Register your models here.

from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'date_joined')
    search_fields = ('username', 'email')
    readonly_fields = ('date_joined',)
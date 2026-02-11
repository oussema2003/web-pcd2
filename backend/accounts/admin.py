from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "is_staff", "is_active", "date_joined"]
    list_filter = ["role", "is_staff", "is_active", "date_joined"]
    search_fields = ["email", "username"]
    ordering = ["email"]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Informations supplémentaires", {"fields": ("role",)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Informations supplémentaires", {"fields": ("email", "role")}),
    )

"""
Admin for auth app
"""
from django.contrib import admin
from .models import UserProfile, AuditLog, LoginAttempt


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'mfa_enabled', 'created_at']
    list_filter = ['mfa_enabled', 'organization']
    search_fields = ['user__username', 'user__email']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'action', 'resource_type', 'timestamp', 'success']
    list_filter = ['action', 'resource_type', 'success', 'timestamp']
    search_fields = ['username', 'description', 'resource_id']
    readonly_fields = ['id', 'timestamp']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'timestamp', 'successful']
    list_filter = ['successful', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['timestamp']

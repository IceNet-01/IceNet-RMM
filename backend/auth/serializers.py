"""
Serializers for auth app
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, AuditLog


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['organization', 'mfa_enabled', 'mfa_enforced', 'preferences']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'user', 'username', 'action',
            'resource_type', 'resource_id', 'description',
            'ip_address', 'user_agent', 'success', 'error_message', 'context'
        ]

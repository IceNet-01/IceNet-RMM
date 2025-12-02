"""
Authentication models for IceNet RMM
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(
        'agents.Organization',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )

    # MFA settings
    mfa_enabled = models.BooleanField(default=False)
    mfa_enforced = models.BooleanField(default=False)

    # Preferences
    preferences = models.JSONField(default=dict, blank=True)

    # API tokens
    api_token = models.CharField(max_length=128, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} profile"


class AuditLog(models.Model):
    """Audit log for security and compliance"""

    class Action(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        EXECUTE = 'execute', 'Execute'
        DOWNLOAD = 'download', 'Download'
        VIEW = 'view', 'View'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # User info
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150)  # Store even if user deleted

    # Action details
    action = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=100)  # agent, command, update, etc.
    resource_id = models.CharField(max_length=255, blank=True)
    description = models.TextField()

    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Additional context
    context = models.JSONField(default=dict, blank=True)

    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"


class LoginAttempt(models.Model):
    """Track login attempts for security"""
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    successful = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]

    def __str__(self):
        status = 'Success' if self.successful else 'Failed'
        return f"{self.username} - {status} - {self.timestamp}"

"""
Agent models for IceNet RMM
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Organization(models.Model):
    """Multi-tenancy support - organizations/clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Settings
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name


class Agent(models.Model):
    """Represents an agent installed on an endpoint"""

    class OS(models.TextChoices):
        WINDOWS = 'windows', 'Windows'
        LINUX = 'linux', 'Linux'
        MACOS = 'macos', 'macOS'

    class Status(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'
        ERROR = 'error', 'Error'
        INSTALLING = 'installing', 'Installing'
        UPDATING = 'updating', 'Updating'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='agents'
    )

    # Basic Information
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)

    # Operating System
    os_type = models.CharField(max_length=20, choices=OS.choices)
    os_name = models.CharField(max_length=255, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    os_arch = models.CharField(max_length=20, blank=True)  # x86_64, arm64, etc.

    # Agent Information
    agent_version = models.CharField(max_length=50)
    agent_build = models.CharField(max_length=100, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INSTALLING
    )
    last_seen = models.DateTimeField(null=True, blank=True)
    last_check_in = models.DateTimeField(null=True, blank=True)

    # Hardware Information
    cpu_model = models.CharField(max_length=255, blank=True)
    cpu_cores = models.IntegerField(null=True, blank=True)
    total_ram = models.BigIntegerField(null=True, blank=True)  # in bytes
    total_disk = models.BigIntegerField(null=True, blank=True)  # in bytes

    # Security
    certificate = models.TextField(blank=True)  # Client certificate for mTLS
    certificate_fingerprint = models.CharField(max_length=128, unique=True)
    certificate_expires = models.DateTimeField(null=True, blank=True)

    # Registration
    registration_token = models.CharField(max_length=255, blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_agents'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-last_seen', 'hostname']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['last_seen']),
            models.Index(fields=['certificate_fingerprint']),
        ]
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        unique_together = [['organization', 'hostname']]

    def __str__(self):
        return f"{self.hostname} ({self.get_os_type_display()})"

    def is_online(self):
        """Check if agent is online based on last_seen"""
        if not self.last_seen:
            return False
        from django.conf import settings
        threshold = timezone.now() - timezone.timedelta(
            seconds=settings.AGENT_OFFLINE_THRESHOLD
        )
        return self.last_seen > threshold

    def update_status(self):
        """Update agent status based on last_seen"""
        if self.is_online():
            if self.status == self.Status.OFFLINE:
                self.status = self.Status.ONLINE
                self.save(update_fields=['status'])
        else:
            if self.status == self.Status.ONLINE:
                self.status = self.Status.OFFLINE
                self.save(update_fields=['status'])


class AgentMetric(models.Model):
    """Time-series metrics from agents"""

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # CPU metrics
    cpu_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    cpu_temp = models.FloatField(null=True, blank=True)

    # Memory metrics
    ram_used = models.BigIntegerField()  # bytes
    ram_total = models.BigIntegerField()  # bytes
    ram_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    # Disk metrics
    disk_used = models.BigIntegerField()  # bytes
    disk_total = models.BigIntegerField()  # bytes
    disk_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    # Network metrics (bytes)
    net_bytes_sent = models.BigIntegerField(default=0)
    net_bytes_recv = models.BigIntegerField(default=0)

    # Process count
    process_count = models.IntegerField(default=0)

    # Additional metrics
    extra_metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Agent Metric'
        verbose_name_plural = 'Agent Metrics'

    def __str__(self):
        return f"{self.agent.hostname} - {self.timestamp}"


class InstalledSoftware(models.Model):
    """Software installed on agents"""

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='software')

    name = models.CharField(max_length=255)
    version = models.CharField(max_length=100, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    install_date = models.DateField(null=True, blank=True)
    install_location = models.CharField(max_length=500, blank=True)
    size = models.BigIntegerField(null=True, blank=True)  # bytes

    # Update status
    update_available = models.BooleanField(default=False)
    latest_version = models.CharField(max_length=100, blank=True)

    # Timestamps
    discovered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional info
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['agent', 'name']),
            models.Index(fields=['update_available']),
        ]
        verbose_name = 'Installed Software'
        verbose_name_plural = 'Installed Software'
        unique_together = [['agent', 'name', 'version']]

    def __str__(self):
        return f"{self.name} {self.version} on {self.agent.hostname}"


class AgentCommand(models.Model):
    """Commands sent to agents"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        TIMEOUT = 'timeout', 'Timeout'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='commands')

    # Command details
    command_type = models.CharField(max_length=100)  # script, update, reboot, etc.
    command = models.TextField()
    parameters = models.JSONField(default=dict, blank=True)

    # Execution
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='commands_created'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Timeout
    timeout_seconds = models.IntegerField(default=300)  # 5 minutes default

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Agent Command'
        verbose_name_plural = 'Agent Commands'

    def __str__(self):
        return f"{self.command_type} on {self.agent.hostname} - {self.status}"


class AgentLog(models.Model):
    """Logs from agents"""

    class Level(models.TextChoices):
        DEBUG = 'debug', 'Debug'
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Critical'

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='logs')

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    source = models.CharField(max_length=100, blank=True)  # Which component logged
    message = models.TextField()

    # Additional context
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', '-timestamp']),
            models.Index(fields=['level', '-timestamp']),
        ]
        verbose_name = 'Agent Log'
        verbose_name_plural = 'Agent Logs'

    def __str__(self):
        return f"{self.agent.hostname} - {self.level} - {self.timestamp}"

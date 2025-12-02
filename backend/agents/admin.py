"""
Django admin for agents app
"""
from django.contrib import admin
from .models import (
    Organization,
    Agent,
    AgentMetric,
    InstalledSoftware,
    AgentCommand,
    AgentLog
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'hostname', 'organization', 'os_type', 'status',
        'last_seen', 'agent_version'
    ]
    list_filter = ['status', 'os_type', 'organization', 'created_at']
    search_fields = ['hostname', 'ip_address', 'mac_address']
    readonly_fields = [
        'id', 'certificate_fingerprint', 'last_seen',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'hostname', 'ip_address', 'mac_address')
        }),
        ('Operating System', {
            'fields': ('os_type', 'os_name', 'os_version', 'os_arch')
        }),
        ('Agent Info', {
            'fields': ('agent_version', 'agent_build', 'status', 'last_seen')
        }),
        ('Hardware', {
            'fields': ('cpu_model', 'cpu_cores', 'total_ram', 'total_disk')
        }),
        ('Security', {
            'fields': (
                'certificate_fingerprint', 'certificate_expires',
                'registration_token', 'registered_at', 'registered_by'
            )
        }),
        ('Metadata', {
            'fields': ('metadata', 'tags'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AgentMetric)
class AgentMetricAdmin(admin.ModelAdmin):
    list_display = ['agent', 'timestamp', 'cpu_percent', 'ram_percent', 'disk_percent']
    list_filter = ['timestamp', 'agent']
    readonly_fields = ['id', 'timestamp']


@admin.register(InstalledSoftware)
class InstalledSoftwareAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'agent', 'update_available', 'discovered_at']
    list_filter = ['update_available', 'discovered_at']
    search_fields = ['name', 'publisher', 'version']


@admin.register(AgentCommand)
class AgentCommandAdmin(admin.ModelAdmin):
    list_display = [
        'agent', 'command_type', 'status',
        'created_by', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'command_type', 'created_at']
    readonly_fields = [
        'id', 'created_at', 'sent_at',
        'started_at', 'completed_at'
    ]
    search_fields = ['agent__hostname', 'command']


@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ['agent', 'level', 'timestamp', 'source', 'message']
    list_filter = ['level', 'timestamp', 'source']
    search_fields = ['agent__hostname', 'message']
    readonly_fields = ['id', 'timestamp']

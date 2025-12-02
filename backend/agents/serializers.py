"""
Serializers for Agent models
"""
from rest_framework import serializers
from .models import (
    Organization,
    Agent,
    AgentMetric,
    InstalledSoftware,
    AgentCommand,
    AgentLog
)


class OrganizationSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description',
            'is_active', 'agent_count', 'settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_agent_count(self, obj):
        return obj.agents.filter(status=Agent.Status.ONLINE).count()


class AgentSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id', 'organization', 'organization_name',
            'hostname', 'ip_address', 'mac_address',
            'os_type', 'os_name', 'os_version', 'os_arch',
            'agent_version', 'agent_build',
            'status', 'is_online', 'last_seen', 'last_check_in',
            'cpu_model', 'cpu_cores', 'total_ram', 'total_disk',
            'certificate_fingerprint', 'certificate_expires',
            'registered_at', 'registered_by',
            'created_at', 'updated_at',
            'metadata', 'tags'
        ]
        read_only_fields = [
            'id', 'status', 'last_seen', 'last_check_in',
            'certificate_fingerprint', 'certificate_expires',
            'registered_at', 'created_at', 'updated_at'
        ]

    def get_is_online(self, obj):
        return obj.is_online()


class AgentDetailSerializer(AgentSerializer):
    """Detailed agent info with stats"""
    software_count = serializers.SerializerMethodField()
    pending_commands = serializers.SerializerMethodField()
    last_metric = serializers.SerializerMethodField()

    class Meta(AgentSerializer.Meta):
        fields = AgentSerializer.Meta.fields + [
            'software_count', 'pending_commands', 'last_metric'
        ]

    def get_software_count(self, obj):
        return obj.software.count()

    def get_pending_commands(self, obj):
        return obj.commands.filter(
            status__in=[AgentCommand.Status.PENDING, AgentCommand.Status.SENT]
        ).count()

    def get_last_metric(self, obj):
        metric = obj.metrics.first()
        if metric:
            return AgentMetricSerializer(metric).data
        return None


class AgentMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMetric
        fields = [
            'id', 'agent', 'timestamp',
            'cpu_percent', 'cpu_temp',
            'ram_used', 'ram_total', 'ram_percent',
            'disk_used', 'disk_total', 'disk_percent',
            'net_bytes_sent', 'net_bytes_recv',
            'process_count', 'extra_metrics'
        ]
        read_only_fields = ['id', 'timestamp']


class InstalledSoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstalledSoftware
        fields = [
            'id', 'agent', 'name', 'version', 'publisher',
            'install_date', 'install_location', 'size',
            'update_available', 'latest_version',
            'discovered_at', 'updated_at', 'metadata'
        ]
        read_only_fields = ['id', 'discovered_at', 'updated_at']


class AgentCommandSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = AgentCommand
        fields = [
            'id', 'agent', 'agent_hostname',
            'command_type', 'command', 'parameters',
            'status', 'output', 'error', 'exit_code',
            'created_by', 'created_by_username',
            'created_at', 'sent_at', 'started_at', 'completed_at',
            'timeout_seconds', 'duration'
        ]
        read_only_fields = [
            'id', 'status', 'output', 'error', 'exit_code',
            'sent_at', 'started_at', 'completed_at'
        ]

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class AgentLogSerializer(serializers.ModelSerializer):
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)

    class Meta:
        model = AgentLog
        fields = [
            'id', 'agent', 'agent_hostname',
            'timestamp', 'level', 'source', 'message', 'context'
        ]
        read_only_fields = ['id', 'timestamp']

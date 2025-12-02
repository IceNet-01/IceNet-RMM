"""
API Views for Agent Management
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg

from .models import (
    Organization,
    Agent,
    AgentMetric,
    InstalledSoftware,
    AgentCommand,
    AgentLog
)
from .serializers import (
    OrganizationSerializer,
    AgentSerializer,
    AgentDetailSerializer,
    AgentMetricSerializer,
    InstalledSoftwareSerializer,
    AgentCommandSerializer,
    AgentLogSerializer
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """Organization management"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get organization statistics"""
        org = self.get_object()
        agents = org.agents.all()

        stats = {
            'total_agents': agents.count(),
            'online_agents': agents.filter(status=Agent.Status.ONLINE).count(),
            'offline_agents': agents.filter(status=Agent.Status.OFFLINE).count(),
            'error_agents': agents.filter(status=Agent.Status.ERROR).count(),
            'windows_agents': agents.filter(os_type=Agent.OS.WINDOWS).count(),
            'linux_agents': agents.filter(os_type=Agent.OS.LINUX).count(),
            'pending_commands': AgentCommand.objects.filter(
                agent__organization=org,
                status__in=[AgentCommand.Status.PENDING, AgentCommand.Status.SENT]
            ).count(),
        }

        return Response(stats)


class AgentViewSet(viewsets.ModelViewSet):
    """Agent management"""
    queryset = Agent.objects.select_related('organization', 'registered_by')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'os_type', 'status']
    search_fields = ['hostname', 'ip_address', 'mac_address']
    ordering_fields = ['hostname', 'last_seen', 'created_at']
    ordering = ['-last_seen']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgentDetailSerializer
        return AgentSerializer

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get agent metrics (time series)"""
        agent = self.get_object()
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timezone.timedelta(hours=hours)

        metrics = AgentMetric.objects.filter(
            agent=agent,
            timestamp__gte=since
        ).order_by('timestamp')

        serializer = AgentMetricSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def software(self, request, pk=None):
        """Get installed software"""
        agent = self.get_object()
        software = agent.software.all()

        # Filter options
        updates_only = request.query_params.get('updates_only', 'false') == 'true'
        if updates_only:
            software = software.filter(update_available=True)

        serializer = InstalledSoftwareSerializer(software, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get agent logs"""
        agent = self.get_object()
        logs = agent.logs.all()

        # Filter by level
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)

        # Limit results
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]

        serializer = AgentLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute_command(self, request, pk=None):
        """Execute a command on the agent"""
        agent = self.get_object()

        command = AgentCommand.objects.create(
            agent=agent,
            command_type=request.data.get('command_type'),
            command=request.data.get('command'),
            parameters=request.data.get('parameters', {}),
            timeout_seconds=request.data.get('timeout_seconds', 300),
            created_by=request.user
        )

        # Send command via NATS (handled by signal)
        serializer = AgentCommandSerializer(command)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reboot(self, request, pk=None):
        """Reboot the agent"""
        agent = self.get_object()

        command = AgentCommand.objects.create(
            agent=agent,
            command_type='reboot',
            command='reboot',
            parameters={'delay': request.data.get('delay', 60)},
            created_by=request.user
        )

        serializer = AgentCommandSerializer(command)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard overview of all agents"""
        agents = self.get_queryset()

        # Filter by organization if specified
        org_id = request.query_params.get('organization')
        if org_id:
            agents = agents.filter(organization_id=org_id)

        dashboard_data = {
            'total': agents.count(),
            'online': agents.filter(status=Agent.Status.ONLINE).count(),
            'offline': agents.filter(status=Agent.Status.OFFLINE).count(),
            'error': agents.filter(status=Agent.Status.ERROR).count(),
            'by_os': {
                'windows': agents.filter(os_type=Agent.OS.WINDOWS).count(),
                'linux': agents.filter(os_type=Agent.OS.LINUX).count(),
            },
            'recent_offline': AgentSerializer(
                agents.filter(status=Agent.Status.OFFLINE).order_by('-last_seen')[:10],
                many=True
            ).data,
        }

        return Response(dashboard_data)


class AgentCommandViewSet(viewsets.ModelViewSet):
    """Agent command management"""
    queryset = AgentCommand.objects.select_related('agent', 'created_by')
    serializer_class = AgentCommandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['agent', 'status', 'command_type']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending command"""
        command = self.get_object()

        if command.status in [AgentCommand.Status.COMPLETED, AgentCommand.Status.FAILED]:
            return Response(
                {'error': 'Cannot cancel completed or failed command'},
                status=status.HTTP_400_BAD_REQUEST
            )

        command.status = AgentCommand.Status.CANCELLED
        command.save()

        serializer = self.get_serializer(command)
        return Response(serializer.data)


class AgentMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent metrics (read-only)"""
    queryset = AgentMetric.objects.select_related('agent')
    serializer_class = AgentMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['agent']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get aggregated statistics"""
        agent_id = request.query_params.get('agent')
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timezone.timedelta(hours=hours)

        metrics = self.get_queryset().filter(timestamp__gte=since)

        if agent_id:
            metrics = metrics.filter(agent_id=agent_id)

        stats = metrics.aggregate(
            avg_cpu=Avg('cpu_percent'),
            avg_ram=Avg('ram_percent'),
            avg_disk=Avg('disk_percent'),
        )

        return Response(stats)


class InstalledSoftwareViewSet(viewsets.ModelViewSet):
    """Installed software management"""
    queryset = InstalledSoftware.objects.select_related('agent')
    serializer_class = InstalledSoftwareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['agent', 'update_available']
    search_fields = ['name', 'publisher', 'version']
    ordering_fields = ['name', 'install_date', 'discovered_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def updates_available(self, request):
        """Get all software with updates available"""
        software = self.get_queryset().filter(update_available=True)

        # Group by software name
        org_id = request.query_params.get('organization')
        if org_id:
            software = software.filter(agent__organization_id=org_id)

        serializer = self.get_serializer(software, many=True)
        return Response(serializer.data)


class AgentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent logs (read-only)"""
    queryset = AgentLog.objects.select_related('agent')
    serializer_class = AgentLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['agent', 'level']
    search_fields = ['message', 'source']
    ordering = ['-timestamp']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Limit to last 7 days by default
        days = int(self.request.query_params.get('days', 7))
        since = timezone.now() - timezone.timedelta(days=days)
        queryset = queryset.filter(timestamp__gte=since)

        return queryset

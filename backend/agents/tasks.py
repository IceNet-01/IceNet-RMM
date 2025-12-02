"""
Celery tasks for agent management
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger('icenet.agents')


@shared_task
def check_agent_health():
    """Check agent health and update status"""
    from .models import Agent

    threshold = timezone.now() - timedelta(
        seconds=settings.AGENT_OFFLINE_THRESHOLD
    )

    # Mark agents as offline if they haven't checked in
    offline_agents = Agent.objects.filter(
        status=Agent.Status.ONLINE,
        last_seen__lt=threshold
    )

    count = offline_agents.update(status=Agent.Status.OFFLINE)

    if count > 0:
        logger.warning(f"Marked {count} agents as offline")

    return f"Checked agent health, {count} agents marked offline"


@shared_task
def rotate_certificates():
    """Rotate agent certificates that are expiring soon"""
    from .models import Agent

    # Find certificates expiring in next 30 days
    expiry_threshold = timezone.now() + timedelta(days=30)

    expiring = Agent.objects.filter(
        certificate_expires__lte=expiry_threshold,
        status__in=[Agent.Status.ONLINE, Agent.Status.OFFLINE]
    )

    count = 0
    for agent in expiring:
        # TODO: Generate new certificate and send to agent
        logger.info(f"Certificate for {agent.hostname} needs rotation")
        count += 1

    return f"Found {count} certificates needing rotation"


@shared_task
def cleanup_old_metrics():
    """Clean up old agent metrics"""
    from .models import AgentMetric

    # Keep metrics for 90 days
    cutoff = timezone.now() - timedelta(days=90)

    deleted_count, _ = AgentMetric.objects.filter(
        timestamp__lt=cutoff
    ).delete()

    logger.info(f"Deleted {deleted_count} old metrics")
    return f"Deleted {deleted_count} old metrics"


@shared_task
def sync_agent_software(agent_id):
    """Sync installed software for an agent"""
    from .models import Agent

    try:
        agent = Agent.objects.get(id=agent_id)

        # TODO: Request software inventory from agent via NATS
        logger.info(f"Requesting software inventory from {agent.hostname}")

        return f"Software sync requested for {agent.hostname}"
    except Agent.DoesNotExist:
        logger.error(f"Agent {agent_id} not found")
        return f"Agent {agent_id} not found"

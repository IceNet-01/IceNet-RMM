"""
Signals for agent app
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Agent, AgentCommand
import logging

logger = logging.getLogger('icenet.agents')


@receiver(post_save, sender=Agent)
def agent_status_changed(sender, instance, created, **kwargs):
    """Log when agent status changes"""
    if created:
        logger.info(f"New agent registered: {instance.hostname} ({instance.id})")
    elif instance.status == Agent.Status.OFFLINE:
        logger.warning(f"Agent offline: {instance.hostname} ({instance.id})")
    elif instance.status == Agent.Status.ERROR:
        logger.error(f"Agent error: {instance.hostname} ({instance.id})")


@receiver(post_save, sender=AgentCommand)
def command_created(sender, instance, created, **kwargs):
    """Send command to agent via NATS when created"""
    if created:
        logger.info(
            f"Command created: {instance.command_type} for {instance.agent.hostname}"
        )
        # TODO: Send to NATS
        # This will be implemented in the NATS integration
        instance.sent_at = timezone.now()
        instance.status = AgentCommand.Status.SENT
        instance.save(update_fields=['sent_at', 'status'])

"""
Celery configuration for IceNet RMM
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('icenet_rmm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'check-agent-health': {
        'task': 'agents.tasks.check_agent_health',
        'schedule': 60.0,  # Every minute
    },
    'collect-agent-metrics': {
        'task': 'monitoring.tasks.collect_metrics',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-for-updates': {
        'task': 'updates.tasks.check_for_updates',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'cleanup-old-logs': {
        'task': 'monitoring.tasks.cleanup_old_logs',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
    'rotate-agent-certificates': {
        'task': 'agents.tasks.rotate_certificates',
        'schedule': crontab(minute=0, hour=0),  # Daily at midnight
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')

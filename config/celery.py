import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("library_ms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily_overdue_check': {
        'task': 'apps.notifications.tasks.daily_overdue_check',
        'schedule': crontab(hour=8, minute=0),
    },
    'hourly_backup_runner': {
        'task': 'apps.notifications.tasks.hourly_backup_runner',
        'schedule': crontab(minute=0),
    }
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.loans.models import Loan

from .services import NotificationService, SystemAlertService


@shared_task
def check_overdue_loans():
    overdue_loans = Loan.objects.filter(
        checkout_date__lt=timezone.now().date() - timedelta(days=30)
    ).exclude(status=Loan.Status.RETURNED)

    if overdue_loans.exists():
        return NotificationService.notify_overdue(list(overdue_loans))

    return {"chat": False, "count": 0}


@shared_task
def check_due_soon_loans():
    due_soon_loans = Loan.objects.filter(
        status=Loan.Status.ACTIVE,
        checkout_date__lte=timezone.now().date() - timedelta(days=25),
    ).exclude(checkout_date__lt=timezone.now().date() - timedelta(days=30))

    if due_soon_loans.exists():
        return NotificationService.notify_due_soon(list(due_soon_loans))

    return {"chat": False, "count": 0}


@shared_task
def daily_overdue_check():
    overdue_results = check_overdue_loans()
    due_soon_results = check_due_soon_loans()

    return {
        "overdue": overdue_results,
        "due_soon": due_soon_results,
    }


@shared_task
def daily_database_backup():
    from .models import LibrarySettings
    from .services import BackupService

    settings_obj = LibrarySettings.get_active()
    if not settings_obj or not settings_obj.backup_enabled:
        return {"skipped": True, "reason": "Backup disabled"}

    backup_service = BackupService()

    valid, error = backup_service.validate_mount()
    if not valid:
        SystemAlertService.alert_mount_unavailable(
            settings_obj.backup_mount_type, settings_obj.backup_mount_path
        )
        return {"success": False, "error": f"Mount unavailable: {error}"}

    try:
        result = backup_service.create_backup()
        if result["success"]:
            deleted = backup_service.cleanup_old_backups()
            SystemAlertService.alert_backup_success(result)
            return {"success": True, "backup": result, "deleted": len(deleted)}
        else:
            SystemAlertService.alert_backup_failure(
                result.get("error", "Unknown error")
            )
            return {"success": False, "error": result.get("error")}
    except Exception as e:
        SystemAlertService.alert_backup_failure(str(e))
        return {"success": False, "error": str(e)}


@shared_task
def hourly_backup_runner():
    from .models import LibrarySettings

    settings_obj = LibrarySettings.get_active()
    if not settings_obj or not settings_obj.backup_enabled:
        return {"skipped": True, "reason": "Backup disabled"}

    current_hour = timezone.now().hour
    if current_hour == settings_obj.backup_hour:
        daily_database_backup.delay()
        return {"success": True, "action": "Backup triggered"}

    return {"skipped": True, "reason": f"Not backup hour (current: {current_hour}, expected: {settings_obj.backup_hour})"}

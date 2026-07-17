from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render

from apps.utils import is_superadmin

from .models import LibrarySettings


@login_required
@user_passes_test(is_superadmin)
def settings(request):
    return render(request, "notifications/settings.html")


@login_required
@user_passes_test(is_superadmin)
def backup_list(request):
    from .services import BackupService

    settings_obj = LibrarySettings.get_active()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_backup":
            settings_obj.backup_enabled = request.POST.get("backup_enabled") == "on"

            try:
                backup_hour = int(request.POST.get("backup_hour", 2))
                if not 0 <= backup_hour <= 23:
                    backup_hour = 2
                settings_obj.backup_hour = backup_hour
            except ValueError:
                settings_obj.backup_hour = 2

            try:
                retention_days = int(request.POST.get("backup_retention_days", 14))
                if not 1 <= retention_days <= 365:
                    retention_days = 14
                settings_obj.backup_retention_days = retention_days
            except ValueError:
                settings_obj.backup_retention_days = 14

            settings_obj.backup_mount_type = request.POST.get(
                "backup_mount_type", "local"
            )
            settings_obj.backup_mount_path = request.POST.get("backup_mount_path", "")
            settings_obj.backup_mount_options = request.POST.get(
                "backup_mount_options", ""
            )
            settings_obj.smb_server = request.POST.get("smb_server", "")
            settings_obj.smb_username = request.POST.get("smb_username", "")
            smb_password = request.POST.get("smb_password", "")
            if smb_password:
                settings_obj.smb_password = smb_password
            settings_obj.smb_domain = request.POST.get("smb_domain", "")
            settings_obj.save()
            messages.success(request, "Backup settings updated successfully.")
            return redirect("notifications:backup_list")

    backup_service = BackupService()
    backups, diagnostics = backup_service.list_backups_with_diagnostics()
    last_backup = backup_service.get_last_backup_info()
    hours = list(range(24))

    return render(
        request,
        "notifications/backup_list.html",
        {
            "backups": backups,
            "last_backup": last_backup,
            "backup_diagnostics": diagnostics,
            "settings_obj": settings_obj,
            "hours": hours,
        },
    )


@login_required
@user_passes_test(is_superadmin)
def backup_run(request):
    from .services import BackupService, SystemAlertService

    if request.method == "POST":
        backup_service = BackupService()
        settings_obj = LibrarySettings.get_active()

        if settings_obj.backup_enabled:
            valid, error = backup_service.validate_mount()
            if not valid:
                messages.error(request, f"Backup mount error: {error}")
                SystemAlertService.alert_backup_failure(f"Mount unavailable: {error}")
                return redirect("notifications:backup_list")

        try:
            result = backup_service.create_backup()
            if result["success"]:
                messages.success(request, f"Backup created: {result['path']}")
                SystemAlertService.alert_backup_success(result)
            else:
                messages.error(
                    request, f"Backup failed: {result.get('error', 'Unknown error')}"
                )
                SystemAlertService.alert_backup_failure(
                    result.get("error", "Unknown error")
                )
        except Exception as e:
            messages.error(request, f"Backup failed: {str(e)}")
            SystemAlertService.alert_backup_failure(str(e))

        return redirect("notifications:backup_list")

    return redirect("notifications:backup_list")


@login_required
@user_passes_test(is_superadmin)
def backup_validate(request):
    from .services import BackupService

    if request.method == "POST":
        backup_service = BackupService()
        valid, error = backup_service.validate_mount()
        if valid:
            messages.success(
                request,
                "Backup storage validation successful. SMB/NFS path is reachable and writable.",
            )
        else:
            messages.error(request, f"Backup validation failed: {error}")

    return redirect("notifications:backup_list")


@login_required
@user_passes_test(is_superadmin)
def backup_download(request, filename):
    from .services import BackupService

    if not filename.startswith("library_backup_") or not filename.endswith(".tar.gz"):
        raise Http404("Invalid filename")

    backup_service = BackupService()
    backup_dir = backup_service.get_backup_dir()
    backup_path = (backup_dir / filename).resolve()

    if not str(backup_path).startswith(str(backup_dir.resolve())):
        raise Http404("Invalid filename")

    if not backup_path.exists():
        raise Http404("Backup not found")

    response = FileResponse(
        open(backup_path, "rb"), as_attachment=True, filename=filename
    )
    return response


@login_required
def session_ping(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    return JsonResponse({"ok": True})

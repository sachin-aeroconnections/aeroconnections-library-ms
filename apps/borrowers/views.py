import csv
import io
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.loans.models import ActivityLog, Loan, ReturnNote
from apps.utils import is_superadmin
from apps.utils.activity_logger import log_activity

from .models import Borrower

logger = logging.getLogger(__name__)


@login_required
def borrower_list(request):
    status_filter = request.GET.get("status", "active")
    search_query = request.GET.get("q")
    employment_filter = request.GET.get("employment_type")

    borrowers = Borrower.objects.filter()

    if status_filter == "active":
        borrowers = borrowers.filter(is_active=True)
    elif status_filter == "inactive":
        borrowers = borrowers.filter(is_active=False)

    if employment_filter:
        borrowers = borrowers.filter(employment_type=employment_filter)

    if search_query:
        borrowers = borrowers.filter(
            full_name__icontains=search_query
        ) | borrowers.filter(email__icontains=search_query)

    paginator = Paginator(borrowers, 10)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    pagination_query = request.GET.copy()
    pagination_query.pop("page", None)

    return render(
        request,
        "borrowers/borrower_list.html",
        {
            "borrowers": page_obj,
            "status_filter": status_filter or "active",
            "page_obj": page_obj,
            "paginator": paginator,
            "pagination_query": pagination_query.urlencode(),
        },
    )


@login_required
@user_passes_test(is_superadmin)
def borrower_delete(request, pk):
    borrower = get_object_or_404(Borrower, pk=pk)

    has_open_loans = Loan.objects.filter(
        borrower_name=borrower.full_name,
        status__in=["active", "overdue"],
    ).exists()

    if has_open_loans:
        messages.error(
            request,
            "Cannot delete this borrower because they still have active or overdue loans.",
        )
        return redirect("borrowers:borrower_detail", pk=borrower.pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text", "").upper()
        if confirm_text != "DELETE":
            messages.error(request, 'Please type "DELETE" to confirm.')
            return redirect("borrowers:borrower_delete", pk=borrower.pk)

        borrower_name = borrower.full_name
        borrower_email = borrower.email
        borrower.delete()

        log_activity(
            ActivityLog.Action.BORROWER_DEACTIVATED,
            f"Borrower '{borrower_name}' ({borrower_email}) permanently deleted",
            request.user,
        )
        messages.success(request, f"Borrower '{borrower_name}' deleted successfully.")
        return redirect("borrowers:borrower_list")

    return render(
        request,
        "borrowers/borrower_confirm_permanent_delete.html",
        {"borrower": borrower},
    )


@login_required
def borrower_create(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        employment_type = request.POST.get(
            "employment_type", Borrower.EmploymentType.PERMANENT
        )
        guardian_name = request.POST.get("guardian_name", "")
        guardian_contact = request.POST.get("guardian_contact", "")

        borrower = Borrower(
            full_name=full_name,
            email=email,
            phone=phone,
            employment_type=employment_type,
            guardian_name=guardian_name,
            guardian_contact=guardian_contact,
        )
        borrower.save()

        log_activity(
            ActivityLog.Action.BORROWER_CREATED,
            f"Borrower '{full_name}' added ({borrower.get_employment_type_display()})",
            request.user,
        )
        messages.success(request, f"Borrower '{full_name}' added successfully.")
        return redirect("borrowers:borrower_list")

    return render(request, "borrowers/borrower_form.html", {"borrower": None})


@login_required
def borrower_detail(request, pk):
    borrower = get_object_or_404(Borrower, pk=pk)
    loans = (
        Loan.objects.filter(borrower_name=borrower.full_name)
        .select_related("book_copy", "created_by")
        .order_by("-checkout_date")
    )
    return_notes = (
        ReturnNote.objects.filter(borrower_name=borrower.full_name)
        .select_related("book_copy", "created_by")
        .order_by("-created_at")
    )
    return render(
        request,
        "borrowers/borrower_detail.html",
        {
            "borrower": borrower,
            "loans": loans,
            "return_notes": return_notes,
        },
    )


@login_required
def borrower_edit(request, pk):
    borrower = get_object_or_404(Borrower, pk=pk)

    if request.method == "POST":
        borrower.full_name = request.POST.get("full_name")
        borrower.email = request.POST.get("email")
        borrower.phone = request.POST.get("phone")
        borrower.employment_type = request.POST.get(
            "employment_type", Borrower.EmploymentType.PERMANENT
        )
        borrower.guardian_name = request.POST.get("guardian_name", "")
        borrower.guardian_contact = request.POST.get("guardian_contact", "")
        borrower.save()

        log_activity(
            ActivityLog.Action.BORROWER_UPDATED,
            f"Borrower '{borrower.full_name}' updated",
            request.user,
        )

        messages.success(
            request, f"Borrower '{borrower.full_name}' updated successfully."
        )
        return redirect("borrowers:borrower_detail", pk=borrower.pk)

    return render(request, "borrowers/borrower_form.html", {"borrower": borrower})


@login_required
def borrower_deactivate(request, pk):
    borrower = get_object_or_404(Borrower, pk=pk)

    if request.method == "POST":
        borrower.is_active = False
        borrower.save()

        log_activity(
            ActivityLog.Action.BORROWER_DEACTIVATED,
            f"Borrower '{borrower.full_name}' deactivated",
            request.user,
        )
        messages.success(request, f"Borrower '{borrower.full_name}' deactivated.")
        return redirect("borrowers:borrower_list")

    return render(
        request, "borrowers/borrower_confirm_delete.html", {"borrower": borrower}
    )


@login_required
def borrower_reactivate(request, pk):
    borrower = get_object_or_404(Borrower, pk=pk)

    if request.method == "POST":
        borrower.is_active = True
        borrower.save()

        log_activity(
            ActivityLog.Action.BORROWER_CREATED,
            f"Borrower '{borrower.full_name}' reactivated",
            request.user,
        )
        messages.success(request, f"Borrower '{borrower.full_name}' reactivated.")
        return redirect("borrowers:borrower_list")

    return render(
        request, "borrowers/borrower_confirm_reactivate.html", {"borrower": borrower}
    )


@login_required
def borrower_import(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect("borrowers:borrower_import")

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File must be a CSV file.")
            return redirect("borrowers:borrower_import")

        decoded_file = csv_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded_file))
        reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames]

        required_fields = ["full_name", "email"]
        if not all(field in reader.fieldnames for field in required_fields):
            messages.error(
                request, f"CSV must have columns: {', '.join(required_fields)}"
            )
            return redirect("borrowers:borrower_import")

        preview_data = {"new": [], "duplicates": [], "errors": []}

        for row_num, row in enumerate(reader, start=2):
            full_name = row.get("full_name", "").strip()
            email = row.get("email", "").strip()
            phone = row.get("phone", "").strip()
            employment_type = row.get("employment_type", "permanent").strip().lower()

            if not full_name or not email:
                preview_data["errors"].append(
                    {"row": row_num, "error": "Full name and email are required"}
                )
                continue

            valid_employment_types = ["permanent", "intern", "temporary"]
            if employment_type not in valid_employment_types:
                employment_type = "permanent"

            borrower_data = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "employment_type": employment_type,
                "row": row_num,
                "json_data": json.dumps(
                    {
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "employment_type": employment_type,
                    }
                ),
            }

            is_duplicate = Borrower.objects.filter(email=email).exists()

            if is_duplicate:
                preview_data["duplicates"].append(borrower_data)
            else:
                preview_data["new"].append(borrower_data)

        return render(
            request, "borrowers/borrower_import.html", {"preview": preview_data}
        )

    return render(request, "borrowers/borrower_import.html")


@login_required
def borrower_import_confirm(request):
    if request.method == "POST":
        borrowers_data = request.POST.getlist("borrowers_data")
        imported_count = 0
        errors = []

        for borrower_json in borrowers_data:
            try:
                data = json.loads(borrower_json)
                full_name = data.get("full_name", "").strip()
                email = data.get("email", "").strip()
                phone = data.get("phone", "").strip()
                employment_type = (
                    data.get("employment_type", "permanent").strip().lower()
                )

                if not full_name or not email:
                    errors.append("Missing required fields for row")
                    continue

                borrower = Borrower(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    employment_type=employment_type,
                )
                borrower.save()
                imported_count += 1
            except json.JSONDecodeError as e:
                errors.append(f"Invalid data format: {e}")
                logger.error(f"Import JSON decode error: {e}")
            except Exception as e:
                errors.append(f"Import failed: {e}")
                logger.error(f"Import error: {e}")

        if imported_count > 0:
            log_activity(
                ActivityLog.Action.BORROWER_CREATED,
                f"Imported {imported_count} borrower(s) via CSV",
                request.user,
            )
            messages.success(
                request, f"Successfully imported {imported_count} borrower(s)."
            )

        if errors:
            messages.warning(request, f"Some rows had issues: {'; '.join(errors[:5])}")

        return redirect("borrowers:borrower_list")

    return redirect("borrowers:borrower_import")

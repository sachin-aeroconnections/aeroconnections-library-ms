from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.books.models import Book, BookCopy
from apps.borrowers.models import Borrower
from apps.utils import is_superadmin
from apps.utils.activity_logger import log_activity

from .models import ActivityLog, Loan, ReturnNote


@login_required
def loan_list(request):
    active_loans_qs = (
        Loan.objects.select_related("book_copy", "book_copy__book")
        .filter(status__in=["active", "overdue"])
        .order_by("checkout_date")
    )
    returned_loans_qs = (
        Loan.objects.select_related("book_copy", "book_copy__book")
        .filter(status="returned")
        .order_by("-checkout_date")
    )

    today = timezone.now().date()
    stats = {
        "total": Loan.objects.count(),
        "active": active_loans_qs.count(),
        "due_soon": Loan.objects.filter(
            status="active", checkout_date__lte=today - timedelta(days=25)
        )
        .exclude(checkout_date__lte=today - timedelta(days=30))
        .count(),
        "overdue": Loan.objects.filter(
            status="active", checkout_date__lte=today - timedelta(days=30)
        ).count(),
    }

    # Paginate active loans
    active_paginator = Paginator(active_loans_qs, 20)
    active_page_number = request.GET.get("active_page")
    active_page = active_paginator.get_page(active_page_number)

    # Paginate returned loans
    returned_paginator = Paginator(returned_loans_qs, 10)
    returned_page_number = request.GET.get("page")
    returned_page = returned_paginator.get_page(returned_page_number)

    pagination_query = request.GET.copy()
    pagination_query.pop("page", None)
    pagination_query.pop("active_page", None)

    return render(
        request,
        "loans/loan_list.html",
        {
            "active_loans": active_page,
            "returned_loans": returned_page,
            "stats": stats,
            "page_obj": returned_page,
            "active_page_obj": active_page,
            "paginator": returned_paginator,
            "active_paginator": active_paginator,
            "pagination_query": pagination_query.urlencode(),
        },
    )


@login_required
def loan_create(request):
    today = timezone.now().date().isoformat()

    if request.method == "POST":
        copy_id = request.POST.get("copy")
        borrower_id = request.POST.get("borrower")
        checkout_date_str = request.POST.get("checkout_date")
        expected_return_str = request.POST.get("expected_return_date")

        book_copy = get_object_or_404(BookCopy, id=copy_id)
        borrower = get_object_or_404(Borrower, id=borrower_id)

        if not borrower.is_active:
            messages.error(request, "This borrower is no longer active.")
            return redirect("loans:loan_create")

        if not book_copy.is_available:
            messages.error(request, f"Copy {book_copy.copy_id} is not available.")
            return redirect("loans:loan_create")

        checkout_date = (
            date.fromisoformat(checkout_date_str)
            if checkout_date_str
            else timezone.now().date()
        )

        due_date = (
            date.fromisoformat(expected_return_str)
            if expected_return_str
            else checkout_date + timedelta(days=Loan.LOAN_DURATION_DAYS)
        )

        Loan.objects.create(
            book_copy=book_copy,
            copy_id_snapshot=book_copy.copy_id,
            book_title_snapshot=book_copy.book.title,
            borrower_name=borrower.full_name,
            checkout_date=checkout_date,
            due_date=due_date,
            created_by=request.user,
        )

        book_copy.status = BookCopy.Status.ON_LOAN
        book_copy.save()

        log_activity(
            ActivityLog.Action.CHECKOUT,
            f"Copy {book_copy.copy_id} ({book_copy.book.title}) checked out to {borrower.full_name}",
            request.user,
        )
        messages.success(
            request, f"Copy {book_copy.copy_id} checked out to {borrower.full_name}."
        )
        return redirect("loans:loan_list")

    borrowers = Borrower.objects.filter(is_active=True)
    available_copies = BookCopy.objects.filter(
        status=BookCopy.Status.AVAILABLE
    ).select_related("book")
    return render(
        request,
        "loans/loan_create.html",
        {"copies": available_copies, "borrowers": borrowers, "today": today},
    )


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    return render(request, "loans/loan_detail.html", {"loan": loan})


@login_required
def loan_return(request, pk):
    loan = get_object_or_404(Loan, pk=pk)

    if loan.status == Loan.Status.RETURNED:
        messages.error(request, "This loan has already been returned.")
        return redirect("loans:loan_list")

    if request.method == "POST":
        return_date = timezone.now().date()
        notes = request.POST.get("notes", "")
        image = request.FILES.get("damage_image")

        loan.return_date = return_date
        loan.status = Loan.Status.RETURNED
        loan.notes = notes
        loan.damage_image = image
        loan.save()

        if notes or image:
            ReturnNote.objects.create(
                loan=loan,
                book_copy=loan.book_copy,
                borrower_name=loan.borrower_name,
                note=notes,
                image=image,
                created_by=request.user,
            )

        loan.book_copy.status = BookCopy.Status.AVAILABLE
        loan.book_copy.save()

        log_activity(
            ActivityLog.Action.RETURN,
            f"Copy {loan.book_copy.copy_id} ({loan.book_copy.book.title}) returned by {loan.borrower_name}",
            request.user,
        )
        messages.success(
            request, f"Copy {loan.book_copy.copy_id} returned successfully."
        )
        return redirect("loans:loan_list")

    return render(request, "loans/loan_return.html", {"loan": loan})


@login_required
def return_notes(request):
    notes = ReturnNote.objects.select_related(
        "book_copy", "book_copy__book", "loan"
    ).all()

    book_filter = request.GET.get("book")
    if book_filter:
        notes = notes.filter(book_copy__copy_id__icontains=book_filter)

    return render(request, "loans/return_notes.html", {"notes": notes})


@login_required
def activity_log(request):
    logs = ActivityLog.objects.select_related("user").all()

    action_filter = request.GET.get("action")
    if action_filter:
        logs = logs.filter(action=action_filter)

    paginator = Paginator(logs, 10)
    page_number = request.GET.get("page")
    try:
        logs_page = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        logs_page = paginator.get_page(1)

    pagination_query = request.GET.copy()
    pagination_query.pop("page", None)

    return render(
        request,
        "loans/activity_log.html",
        {
            "logs": logs_page,
            "page_obj": logs_page,
            "paginator": paginator,
            "pagination_query": pagination_query.urlencode(),
        },
    )


@login_required
def dashboard(request):
    today = timezone.now().date()
    overdue_cutoff = today - timedelta(days=30)
    due_soon_cutoff = today - timedelta(days=25)

    books_count = Book.objects.count()
    copies_count = BookCopy.objects.count()
    active_loans_count = Loan.objects.filter(status__in=["active", "overdue"]).count()

    # Fetch overdue list once and derive count from it
    overdue_list = list(
        Loan.objects.filter(status="active", checkout_date__lte=overdue_cutoff)
        .select_related("book_copy", "book_copy__book")
        .order_by("checkout_date")[:10]
    )
    overdue_count = Loan.objects.filter(
        status="active", checkout_date__lte=overdue_cutoff
    ).count()

    due_soon_loans = Loan.objects.filter(
        status="active", checkout_date__lte=due_soon_cutoff
    ).exclude(checkout_date__lte=overdue_cutoff)

    recent_loans = Loan.objects.select_related(
        "book_copy", "book_copy__book"
    ).order_by("-created_at")[:5]

    stats = {
        "books": books_count,
        "copies": copies_count,
        "active": active_loans_count,
        "overdue": overdue_count,
        "due_soon": due_soon_loans.count(),
    }

    return render(
        request,
        "loans/dashboard.html",
        {
            "stats": stats,
            "recent_loans": recent_loans,
            "overdue_loans": overdue_list,
            "due_soon_loans": due_soon_loans,
        },
    )


@login_required
@user_passes_test(is_superadmin)
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk)

    if loan.status != Loan.Status.RETURNED:
        messages.error(request, "Only returned loans can be deleted.")
        return redirect("loans:loan_detail", pk=loan.pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text", "").upper()
        if confirm_text != "DELETE":
            messages.error(request, 'Please type "DELETE" to confirm.')
            return redirect("loans:loan_delete", pk=loan.pk)

        loan_info = f"{loan.copy_id_snapshot} ({loan.book_title_snapshot}) - {loan.borrower_name}"
        loan.delete()

        log_activity(
            ActivityLog.Action.RETURN, f"Loan record deleted: {loan_info}", request.user
        )
        messages.success(request, "Loan record deleted successfully.")
        return redirect("loans:loan_list")

    return render(request, "loans/loan_confirm_delete.html", {"loan": loan})


@login_required
@user_passes_test(is_superadmin)
def return_note_delete(request, pk):
    note = get_object_or_404(ReturnNote, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text", "").upper()
        if confirm_text != "DELETE":
            messages.error(request, 'Please type "DELETE" to confirm.')
            return redirect("loans:return_note_delete", pk=note.pk)

        note_info = f"{note.book_copy.copy_id} ({note.book_copy.book.title}) - {note.borrower_name}"
        note.delete()

        log_activity(
            ActivityLog.Action.RETURN, f"Return note deleted: {note_info}", request.user
        )
        messages.success(request, "Return note deleted successfully.")
        return redirect("loans:return_notes")

    return render(request, "loans/return_note_confirm_delete.html", {"note": note})

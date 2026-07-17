import csv
import io
import json
import logging

logger = logging.getLogger(__name__)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.loans.models import ActivityLog, Loan, ReturnNote

from .models import Book, BookCopy


@login_required
def book_list(request):
    books = Book.objects.prefetch_related("copies").filter()
    search_query = request.GET.get("q")

    if search_query:
        books = (
            books.filter(title__icontains=search_query)
            | books.filter(author__icontains=search_query)
            | books.filter(book_id__icontains=search_query)
        )

    paginator = Paginator(books, 10)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    pagination_query = request.GET.copy()
    pagination_query.pop("page", None)

    return render(
        request,
        "books/book_list.html",
        {
            "books": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "pagination_query": pagination_query.urlencode(),
        },
    )


@login_required
def book_search_api(request):
    query = request.GET.get("q", "")
    if len(query) < 2:
        return JsonResponse([], safe=False)

    books = Book.objects.filter(title__icontains=query)[:10]
    results = [
        {
            "id": book.pk,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn or "",
        }
        for book in books
    ]
    return JsonResponse(results, safe=False)


@login_required
def book_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        isbn = request.POST.get("isbn", "")
        copies = int(request.POST.get("copies", 1))
        book_id = request.POST.get("book_id", "")

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            book_id=book_id if book_id else None,
        )
        book.save()

        for i in range(copies):
            BookCopy.objects.create(book=book)

        ActivityLog.objects.create(
            action=ActivityLog.Action.BOOK_CREATED,
            description=f"Book #{book.book_id} ({book.title}) added with {copies} copy/copies",
            user=request.user,
        )
        messages.success(
            request, f"Book #{book.book_id} added with {copies} copy/copies."
        )
        return redirect("books:book_list")

    return render(request, "books/book_create.html")


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    copies = book.copies.all()
    loans = (
        Loan.objects.filter(book_copy__in=copies)
        .select_related("book_copy", "created_by")
        .order_by("-checkout_date")
    )
    return_notes = (
        ReturnNote.objects.filter(book_copy__in=copies)
        .select_related("book_copy")
        .order_by("-created_at")
    )
    return render(
        request,
        "books/book_detail.html",
        {
            "book": book,
            "copies": copies,
            "loans": loans,
            "return_notes": return_notes,
        },
    )


@login_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "POST":
        book.title = request.POST.get("title")
        book.author = request.POST.get("author")
        book.isbn = request.POST.get("isbn", "")
        copies_str = request.POST.get("copies", "")
        new_copies = int(copies_str) if copies_str else book.total_copies
        new_book_id = request.POST.get("book_id")
        if new_book_id:
            book.book_id = new_book_id
        book.save()

        current_copies = book.total_copies
        if new_copies > current_copies:
            for i in range(new_copies - current_copies):
                BookCopy.objects.create(book=book)
        elif new_copies < current_copies:
            available_copies = book.copies.filter(status=BookCopy.Status.AVAILABLE)
            excess = current_copies - new_copies
            for copy in available_copies[:excess]:
                copy.delete()

        ActivityLog.objects.create(
            action=ActivityLog.Action.BOOK_UPDATED,
            description=f"Book #{book.book_id} ({book.title}) updated",
            user=request.user,
        )

        messages.success(request, f"Book #{book.book_id} updated successfully.")
        return redirect("books:book_detail", pk=book.pk)

    return render(request, "books/book_edit.html", {"book": book})


@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)

    on_loan = book.copies.filter(status=BookCopy.Status.ON_LOAN).exists()
    if on_loan:
        messages.error(
            request, "Cannot delete a book that has copies currently on loan."
        )
        return redirect("books:book_list")

    if request.method == "POST":
        book_id = book.book_id
        title = book.title
        book.delete()

        ActivityLog.objects.create(
            action=ActivityLog.Action.BOOK_DELETED,
            description=f"Book #{book_id} ({title}) deleted",
            user=request.user,
        )
        messages.success(request, f"Book #{book_id} deleted successfully.")
        return redirect("books:book_list")

    return render(request, "books/book_confirm_delete.html", {"book": book})


@login_required
def copy_create(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)

    if request.method == "POST":
        BookCopy.objects.create(book=book)
        messages.success(request, f"New copy added to {book.title}.")
        return redirect("books:book_detail", pk=book.pk)

    return redirect("books:book_detail", pk=book.pk)


@login_required
def copy_delete(request, book_pk, copy_pk):
    book = get_object_or_404(Book, pk=book_pk)
    copy = get_object_or_404(BookCopy, pk=copy_pk, book=book)

    if copy.status != BookCopy.Status.AVAILABLE:
        messages.error(request, "Cannot delete a copy that is currently on loan.")
        return redirect("books:book_detail", pk=book.pk)

    if request.method == "POST":
        copy_id = copy.copy_id
        copy.delete()
        messages.success(request, f"Copy {copy_id} deleted.")
        return redirect("books:book_detail", pk=book.pk)

    return redirect("books:book_detail", pk=book.pk)


@login_required
def book_import(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect("books:book_import")

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File must be a CSV file.")
            return redirect("books:book_import")

        decoded_file = csv_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded_file))
        reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames]

        required_fields = ["title", "author"]
        if not all(field in reader.fieldnames for field in required_fields):
            messages.error(
                request, f"CSV must have columns: {', '.join(required_fields)}"
            )
            return redirect("books:book_import")

        preview_data = {"new": [], "duplicates": [], "errors": []}

        for row_num, row in enumerate(reader, start=2):
            title = row.get("title", "").strip()
            author = row.get("author", "").strip()
            isbn = row.get("isbn", "").strip()
            copies_str = row.get("copies", "1").strip()

            if not title or not author:
                preview_data["errors"].append(
                    {"row": row_num, "error": "Title and author are required"}
                )
                continue

            try:
                copies = int(copies_str) if copies_str else 1
            except ValueError:
                copies = 1

            book_data = {
                "title": title,
                "author": author,
                "isbn": isbn,
                "copies": copies,
                "row": row_num,
                "json_data": json.dumps(
                    {"title": title, "author": author, "isbn": isbn, "copies": copies}
                ),
            }

            is_duplicate = False
            if isbn:
                if Book.objects.filter(isbn=isbn).exists():
                    is_duplicate = True

            if is_duplicate:
                preview_data["duplicates"].append(book_data)
            else:
                preview_data["new"].append(book_data)

        return render(request, "books/book_import.html", {"preview": preview_data})

    return render(request, "books/book_import.html")


@login_required
def book_import_confirm(request):
    if request.method == "POST":
        books_data = request.POST.getlist("books_data")
        imported_count = 0
        errors = []

        for book_json in books_data:
            try:
                data = json.loads(book_json)
                title = data.get("title", "").strip()
                author = data.get("author", "").strip()
                isbn = data.get("isbn", "").strip()
                copies = data.get("copies", 1)

                if not title or not author:
                    errors.append("Missing required fields for row")
                    continue

                book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                )
                book.save()

                copies = int(copies) if copies else 1
                for _ in range(copies):
                    BookCopy.objects.create(book=book)

                imported_count += 1
            except json.JSONDecodeError as e:
                errors.append(f"Invalid data format: {e}")
                logger.error(f"Import JSON decode error: {e}")
            except Exception as e:
                errors.append(f"Import failed: {e}")
                logger.error(f"Import error: {e}")

        if imported_count > 0:
            ActivityLog.objects.create(
                action=ActivityLog.Action.BOOK_CREATED,
                description=f"Imported {imported_count} book(s) via CSV",
                user=request.user,
            )
            messages.success(
                request, f"Successfully imported {imported_count} book(s)."
            )

        if errors:
            messages.warning(request, f"Some rows had issues: {'; '.join(errors[:5])}")

        return redirect("books:book_list")

    return redirect("books:book_import")

from django.db import models, transaction


class Book(models.Model):
    book_id = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        help_text="Auto-generated internal ID. Can be edited."
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["book_id"]
        verbose_name = "Book Title"
        verbose_name_plural = "Book Titles"

    def __str__(self):
        return f"#{self.book_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.book_id:
            with transaction.atomic():
                last_book = Book.objects.select_for_update().order_by("-book_id").first()
                if last_book and last_book.book_id:
                    try:
                        last_num = int(last_book.book_id)
                        self.book_id = str(last_num + 1).zfill(2)
                    except ValueError:
                        self.book_id = "01"
                else:
                    self.book_id = "01"
        super().save(*args, **kwargs)

    @property
    def total_copies(self):
        return len(self.copies.all())

    @property
    def available_copies(self):
        return len([c for c in self.copies.all() if c.status == BookCopy.Status.AVAILABLE])

    @property
    def on_loan_copies(self):
        return len([c for c in self.copies.all() if c.status == BookCopy.Status.ON_LOAN])


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ON_LOAN = "on_loan", "On Loan"
        DAMAGED = "damaged", "Damaged"
        LOST = "lost", "Lost"
        RETIRED = "retired", "Retired"

    copy_id = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        help_text="Auto-generated unique copy ID (e.g., #01-1, #01-2)"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="copies"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    condition = models.CharField(
        max_length=50,
        blank=True,
        help_text="Condition notes (e.g., 'Good', 'Fair', 'Needs repair')"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["copy_id"]
        verbose_name = "Book Copy"
        verbose_name_plural = "Book Copies"

    def __str__(self):
        return f"{self.book.book_id}-{self.copy_suffix}"

    @property
    def copy_suffix(self):
        if self.copy_id:
            parts = self.copy_id.split("-")
            return parts[-1] if len(parts) > 1 else "1"
        return "1"

    def save(self, *args, **kwargs):
        if not self.copy_id:
            with transaction.atomic():
                book_prefix = self.book.book_id if self.book else "00"
                last_copy = BookCopy.objects.select_for_update().filter(
                    copy_id__startswith=f"{book_prefix}-"
                ).order_by("-copy_id").first()

                if last_copy and last_copy.copy_id:
                    try:
                        suffix = int(last_copy.copy_suffix)
                        self.copy_id = f"{book_prefix}-{suffix + 1}"
                    except ValueError:
                        self.copy_id = f"{book_prefix}-1"
                else:
                    self.copy_id = f"{book_prefix}-1"
        super().save(*args, **kwargs)

    @property
    def current_loan(self):
        return self.loans.filter(status__in=["active", "overdue"]).first()

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def is_on_loan(self):
        return self.status == self.Status.ON_LOAN

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.4.0] - 2026-07-17

### Security
- **Strict Host Verification** - Removed default `ALLOWED_HOSTS=*` from Dockerfile and Docker Compose; enforced explicit environment variable configuration (`ALLOWED_HOSTS`).
- **Setup PIN Authentication** - Enforced secure `check_password` verification for setup PIN (removed insecure plain-text fallback).
- **API Authentication** - Added `@login_required` decorator to `book_search_api` endpoint to prevent unauthenticated access to book data.

### Performance
- **Build-Time Tailwind CSS** - Replaced 380KB render-blocking Tailwind CDN script with a build-time purged and minified CSS compilation (`tailwind.min.css`), reducing cold page render times by 1–3s.
- **Background Animation Reduction** - Optimized `base.html` background layer by reducing particle nodes from 20 to 6, removing high-GPU rotating overlays, and supporting `@media (prefers-reduced-motion: reduce)`.
- **Active Loans Pagination** - Added pagination (`active_page`) to active loans list view and template, eliminating unbounded database fetches.
- **Dashboard Query Consolidation** - Consolidated dashboard stats queries and cached date calculations per request.
- **Branding Context Processor Caching** - Cached `branding_context` processor in memory/Redis for 5 minutes with automatic invalidation on `Branding.save()`.

### Fixed & Improved
- **Concurrent ID Generation** - Wrapped `Book.save()` and `BookCopy.save()` internal ID generation in `transaction.atomic()` with `select_for_update()` to prevent race conditions and duplicate ID collisions.
- **Stale Copy Count Property** - Converted `total_copies`, `available_copies`, and `on_loan_copies` on `Book` from `@cached_property` to `@property` so copy updates reflect immediately in UI views.
- **Automated Overdue Status Sync** - `check_overdue_loans` Celery task now updates loan status to `OVERDUE` in the database automatically.
- **LibrarySettings Wiring** - Integrated `LibrarySettings.loan_duration_days` into checkout due date calculation and enforced `max_books_per_borrower` limit during checkout.

### Maintenance
- **Cleaned Up Unused Settings** - Removed obsolete `STATICFILES` setting from `config/settings.py`.
- **Consolidated Helpers** - Centralized `is_superadmin` view decorator helper into `apps.utils`.

## [1.3.9] - 2026-04-09

### Performance
- **Book Query Optimization** - Replaced filter count with list comprehension for total/available/on-loan copies
- **Book List N+1 Fix** - Added `prefetch_related("copies")` to book_list view

### Fixed
- **Overdue Logic** - Changed `>` to `>=` in `is_overdue` property for correct day-30 detection
- **Due Soon Query** - Fixed dashboard `due_soon_loans` query to use `__lte` instead of `__lt`

### Added
- **Hourly Backup Runner** - New Celery task to trigger backups at configured hour
- **Celery Beat Schedule** - Configured beat for daily overdue checks (8 AM) and hourly backup runner

## [1.3.8] - 2026-03-26

### Security
- **SMB Credential Security** - SMB passwords loaded from file-based secret sources instead of command-line arguments.
- **Path Traversal Hardening** - Backup download validates filename format with prefix/suffix checks.
- **Multi-Stage Dockerfile** - Build dependencies removed from runtime image, reducing attack surface.

### Added
- **Health Endpoint** - New `/health/` endpoint for container orchestration and load balancer health checks.
- **Dockerfile Healthcheck** - Native Docker HEALTHCHECK directive for container monitoring.

### Fixed
- **Celery Task Optimization** - `check_overdue_loans` and `check_due_soon_loans` tasks now use optimized queries.

## [1.3.6] - 2026-03-26

### Fixed
- **Borrowers Redirect Loop** - Replaced `RedirectView` on `/borrowers/` with direct `borrower_list` view to prevent infinite redirect loop.
- **Pagination Query Preservation** - Added `pagination_query` context variable to all paginated views so filter/search params survive page navigation.

### Changed
- **Shared Pagination Template** - Extracted pagination into reusable `templates/includes/pagination.html` shared across loans, borrowers, books, and activity log.
- **Pagination Standardization** - Consistent pagination appearance and behavior across all list views.

## [1.3.5] - 2026-03-26

### Added
- **Superadmin Borrower Deletion** - Superadmins can permanently delete borrower profiles with explicit `DELETE` confirmation.
- **Borrower Delete Safety Guard** - Borrower deletion is blocked when active or overdue loans exist for that borrower.
- **Activity Log Pagination** - Activity log now supports paginated browsing.

### Changed
- **Pagination Size** - Standardized list pagination to 10 items per page (Books, Borrowers, Returned Loans, Activity Log).
- **Borrowers Default Navigation** - Borrowers navigation now defaults to active borrowers.
- **Borrowers List Privacy** - Phone number is hidden in the borrowers list table; full details remain on borrower detail page.
- **Application Version** - Bumped to `1.3.5`.

### Documentation
- **README Refresh** - Updated project status and feature coverage.
- **Known Issues Section** - Added known limitations and operational caveats.
- **Disclaimer Section** - Added operational and responsibility disclaimer.
- **Third-Party Credits** - Added attributions for frameworks, libraries, and assets used by the project.

## [1.3.4] - 2026-03-25

### Added
- **Auto Logout** - Added automatic session expiration with enforced server-side timeouts.
  - Idle timeout: 10 minutes
  - Absolute timeout: 60 minutes
  - Warning modal: 60 seconds before idle logout
  - "Stay signed in" keep-alive action

### Security
- **Session Timeout Middleware** - Enforced idle/absolute session timeout in middleware for authenticated users.
- **Secret Field Hardening** - Admin secret fields now use masked password inputs and preserve existing values when left blank.

### Changed
- **Application Version** - Bumped app version to `1.3.4`.

## [1.3.3] - 2026-03-25

### Security
- **XSS Vulnerabilities Fixed** - Fixed XSS vulnerabilities in templates with inline onclick handlers (add `|escapejs` filter)
- **Pipe Injection Fixed** - Replaced pipe-delimited CSV import data with JSON serialization to prevent injection
- **PIN Security Hardened** - PIN now hashed using Django's `make_password`/`check_password` instead of plain text storage
- **Settings Defaults** - Fixed dangerous DEBUG and ALLOWED_HOSTS defaults; DEBUG now defaults to False
- **Password Masking in Admin** - Sensitive fields (SMB Password, Email Password, Webhook Secret, Setup PIN) are hidden in Django admin forms while still allowing secure resets

### Fixed
- **File Handle Leak** - Fixed file handle leak in backup download endpoint
- **Input Validation** - Added validation for backup settings (hour, retention days)
- **Error Handling** - Improved error handling in CSV imports with proper logging

### Added
- **Pagination** - Added pagination (25 items/page) to book, borrower, and loan list views
- **Database Indexes** - Added indexes on Loan model for checkout_date, status, due_date, borrower_name
- **Security Headers** - Added production security headers (HSTS, CSP, X-Frame-Options, etc.)
- **Shared Activity Logger** - Created reusable activity logger utility

### Changed
- **Settings Page Rework** - Settings page now shows two sections: Backup and Django Admin
- **cached_property** - Book model properties now use `@cached_property` to prevent N+1 queries

## [1.3.2] - 2026-03-24

### Added
- **Backup Listing Diagnostics** - Backup page now shows resolved backup path and discovered/displayed file counts for easier troubleshooting.

### Changed
- **SMB Docs** - Clarified host-mount-first approach for container deployments and added explicit validation guidance.

### Fixed
- **Backup UI Listing** - Fixed backup listing logic so valid files on SMB/local storage are displayed consistently.
- **Timezone Handling** - Replaced fragile UTC conversion in backup listing and retention cleanup with safe timezone-aware handling.
- **Metadata Read Resilience** - Backup files now remain visible even when adjacent metadata parsing fails.

## [1.3.1] - 2026-03-24

### Added
- **Backup Storage Validation** - New `Validate SMB/NFS` action in Settings to verify mount reachability and write access before backup.

### Changed
- **SMB Strategy (Containers)** - Default behavior now prefers host-mounted SMB shares bound into the container path, with explicit guidance for Dockhand deployments.
- **SMB Password Handling** - Password field no longer pre-fills in UI; blank submissions keep existing stored password.

### Fixed
- **Backup Temp Directory** - Temporary backup workspace now uses `/tmp/library-backups` with parent directory creation to avoid missing-path errors.
- **Backup Download Import** - Corrected service import path used by backup download endpoint.
- **SMB Mount Errors** - Clearer error messaging when in-container CIFS mount is blocked due to missing privileged capabilities.

## [1.3.0] - 2026-03-24

### Removed
- **Google Sheets Sync** - Removed due to OAuth complexity issues

### Added
- **Auto-Backup System** - Daily automated database backups
  - Configurable backup time (default: 2 AM)
  - Configurable retention (default: 14 days)
  - Support for Local, NFS, and SMB/CIFS mounts
  - Manual backup trigger option
  - Backup list with download links
- **System Alert Webhook** - Separate webhook for system events
  - Backup success/failure notifications
  - Mount unavailable alerts
  - Independent from loan notification webhook

### Changed
- **Database Path** - Fixed SQLite path from `data/db.sqlite3` to `db.sqlite3`
- **Settings Page** - Replaced Google Sheets with Backup and System Alert configuration

### Fixed
- **OAuth Issues** - Removed problematic OAuth PKCE flow

## [1.2.5] - 2026-03-23

### Fixed
- **OAuth HTTPS Detection** - Added `SECURE_PROXY_SSL_HEADER` for HTTPS detection behind proxies (Tailscale, Cloudflare, etc.)
- **OAuth State Handling** - Fixed state validation and authorization_response URL for proper OAuth flow

### Added
- **App Version Footer** - Version number displayed in footer on all pages
- **Repository Links** - GitHub and Docker Hub links in footer
- **Settings Navbar Link** - Settings page accessible from navbar (superadmin only)

## [1.2.4] - 2026-03-23

### Added
- **Settings Navbar Link** - Settings page accessible from navbar (superadmin only)
- **google-auth-oauthlib** - Added package for OAuth authentication

## [1.2.3] - 2026-03-23

### Added
- **Browser-Based Google Sheets OAuth** - No more manual file copying; authorize directly from browser
- **Auto-Sync on Activity** - Data syncs automatically on book/borrower/loan changes
- **First-Time Sync** - "Create Spreadsheet & Sync All Data" button for initial backup
- **Google Sheets Settings Page** - Dedicated UI at `/settings/sheets/`

### Changed
- **Credentials Storage** - OAuth credentials stored in `/app/data/` for Docker volume persistence

## [1.2.2] - 2026-03-23

### Fixed
- **Borrower Detail** - Fixed FieldError when viewing borrower with loans
- **Borrower Tabs** - Added Active/All/Inactive tabs for better filtering

### Added
- **Editable Checkout Date** - Staff can now set a custom checkout date when creating loans, enabling adding of historical records

## [1.2.1] - 2026-03-23

### Fixed
- **Data Persistence** - Database now stored at `/app/data/` for proper Docker volume mounting
- **Clear All Data Command** - New management command to reset database completely

## [1.2.0] - 2026-03-23

### Added
- **CSV Import - Books** - Bulk import books via CSV file with preview and duplicate detection
- **CSV Import - Borrowers** - Bulk import borrowers via CSV file with preview and duplicate detection
- **Book Search Autocomplete** - Search existing books when adding new books to auto-fill author and ISBN

### Fixed
- **Book Edit** - Copies field now auto-fills with current count to prevent ValueError

## [1.1.0] - 2026-03-22

### Added
- **Setup Wizard** - Guided first-time setup for library name, admin account, and branding
- **PIN Protection** - Setup wizard secured with a 4-digit PIN
- **CSRF_TRUSTED_ORIGINS** - Docker environment variable for domain-based access
- **Setup Security Page** - Change PIN after initial setup

## [1.0.0] - 2026-03-22

### Added
- **Book Copy System** - Each physical book has a unique copy ID (e.g., #01-1, #01-2) for precise tracking
- **Borrower Management** - Full CRUD operations with activation/deactivation support
- **Return Notes** - Optional notes and damage photos attached to returns
- **Activity Log** - Immutable record of all system activities (checkouts, returns, etc.)
- **Configurable Loan Settings** - Adjustable loan duration (14-60 days) and due thresholds
- **Webhook Support** - Configure external webhooks for notifications
- **Email Notifications** - SMTP configuration for email alerts
- **Library Settings** - Admin-configurable settings for loans, notifications, and integrations
- **Modern UI** - Top navigation bar with responsive design and AeroConnections branding
- **Google Sheets Backup** - Sync data to Google Sheets for disaster recovery
- **Test Data Management** - Commands to add/remove test data

### Changed
- **Loan System** - Now links to specific BookCopy instead of Book
- **Dashboard** - Shows book titles with copy IDs for better tracking
- **UI/UX** - Complete redesign with horizontal top navigation

### Fixed
- **Return Notes** - No longer saved when empty
- **Branding** - Company name and library name toggles now work correctly
- **Dashboard** - Copy IDs display correctly in overdue/due soon sections

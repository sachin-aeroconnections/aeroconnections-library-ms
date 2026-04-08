# AeroConnections Library Management System

A free and open-source library management system built with Django.

[![Docker Hub](https://img.shields.io/docker/v/sachinaeroconnections/library-ms?label=docker&style=flat-square)](https://hub.docker.com/r/sachinaeroconnections/library-ms)
[![Docker Hub](https://img.shields.io/docker/pulls/sachinaeroconnections/library-ms?style=flat-square)](https://hub.docker.com/r/sachinaeroconnections/library-ms)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/aeroconnections/aeroconnections-library-ms?style=flat-square)](https://github.com/aeroconnections/aeroconnections-library-ms/releases)

## Features

- **Book Copies** — Each physical book has a unique copy ID (e.g., #01-1, #01-2) for precise tracking
- **Health Endpoint** — `/health/` endpoint for container orchestration and health checks
- **Docker Healthcheck** — Native Docker HEALTHCHECK for container monitoring
- **Loan Management** — Checkout, return, and configurable loan duration (14-60 days)
- **Borrower Management** — Add borrowers with activation/deactivation support
- **Return Notes** — Optional notes and damage photos for returns
- **Activity Log** — Immutable record of all system activities
- **Webhook Support** — Configure webhooks for external notifications (Slack, Discord, Google Chat)
- **Email Notifications** — SMTP configuration for email alerts
- **Auto-Backup** — Automatic daily backups with Local, NFS, or SMB/CIFS storage support
- **System Alerts** — Dedicated webhook for backup status and system notifications
- **Configurable Settings** — Loan duration, due thresholds, max books per borrower
- **Modern UI** — Responsive design with AeroConnections branding
- **Multi-platform** — Supports AMD64 and ARM64 architectures
- **Setup Wizard** — Easy first-time configuration with PIN protection
- **CSV Import** — Bulk import books and borrowers via CSV files
- **Book Autocomplete** — Auto-fill author and ISBN when adding new books
- **Auto Logout** — Automatic logout on inactivity with warning prompt and secure session timeout
- **Pagination** — Consistent 10-items-per-page pagination on major list views
- **Superadmin Controls** — Dedicated destructive actions (with confirmations) for privileged users

## First-Time Setup

### 1. Access the Setup Wizard

After starting the application, navigate to:
```
http://localhost:8000/setup/
```

You will be prompted to enter a Setup PIN. If this is your first time, you can proceed to the setup wizard directly.

### 2. Configure Your Library

Fill in the setup form with:

| Field | Description |
|-------|-------------|
| Library Name | Your library's name |
| Domain(s) | URL(s) where the app will be accessed. Supports multiple domains separated by commas |
| Admin Username | Username for the admin account |
| Admin Email | Email for the admin account |
| Admin Password | Password for the admin account |
| Loan Duration | Default loan period in days (default: 30) |
| Due Soon Threshold | Days before due date to show warning (default: 25) |
| Max Books | Maximum books a borrower can have (default: 5) |
| Setup PIN | PIN to access setup page in the future (4-6 digits) |

### 3. Access the Application

After setup, log in at:
```
http://localhost:8000/accounts/login/
```

## Deployment

### Docker (Recommended)

```bash
docker run -d \
  --name library-ms \
  -p 8000:8000 \
  -v library-data:/app/data \
  sachinaeroconnections/library-ms:latest
```

For docker-compose, the volume is configured automatically:

```bash
curl -O https://raw.githubusercontent.com/aeroconnections/aeroconnections-library-ms/main/docker-compose.yml
docker-compose up -d
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/aeroconnections/aeroconnections-library-ms.git
cd library-ms

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

Then access `/setup/` to configure your library.

## Auto Logout

Auto logout is enabled by default and enforced server-side.

- **Idle timeout**: 10 minutes
- **Absolute timeout**: 60 minutes
- **Warning**: 60 seconds before idle logout

### Environment Variables

```bash
AUTO_LOGOUT_ENABLED=true
AUTO_LOGOUT_IDLE_MINUTES=10
AUTO_LOGOUT_ABSOLUTE_MINUTES=60
AUTO_LOGOUT_WARNING_SECONDS=60
```

Notes:
- Leaving the browser idle beyond the idle timeout logs out the current user session.
- Even with activity, sessions are force-expired at the absolute timeout.
- Auto logout affects authentication/session only; it does not modify books, loans, borrowers, or backup data.

## Auto-Backup

### Configuration

1. Go to **Settings** (`/settings/`) - accessible via navbar for superadmins
2. Enable Auto-Backup
3. Configure backup time (default: 2 AM)
4. Set retention period (default: 14 days)
5. Choose mount type:
   - **Local** - Store backups in container's data directory
   - **NFS** - Network File System mount
   - **SMB/CIFS** - Windows/Samba share

### Mount Configuration

For NFS/SMB mounts, enter the mount path and credentials:

- **Mount Path**: e.g., `/mnt/backups`
- **SMB Server**: e.g., `//netstorage.local/library-backups`
- **SMB Credentials**: Username, password, domain (if required)

### SMB/CIFS Backup Setup

#### Recommended Approach (Containers)

Use a **host-mounted SMB share** and bind it into the container. This is the default and recommended approach because most container platforms do not allow in-container `mount -t cifs` without privileged capabilities.

Why this approach:
- Containerized environments often block `CAP_SYS_ADMIN` required for CIFS mounts.
- Host mount is more stable and easier to debug.
- Backup path validation can verify write access directly.

#### 1. Mount SMB on the host

Install CIFS tools:

```bash
sudo apt update && sudo apt install -y cifs-utils
```

Create credentials file:

```bash
sudo mkdir -p /etc/smb-credentials
sudo nano /etc/smb-credentials/library-backups.cred
```

Credentials file content:

```ini
username=YOUR_SMB_USERNAME
password=YOUR_SMB_PASSWORD
domain=WORKGROUP
```

Secure the file:

```bash
sudo chmod 600 /etc/smb-credentials/library-backups.cred
```

Create mount point and mount share:

```bash
sudo mkdir -p /mnt/Storage/Files/library-backups
sudo mount -t cifs //10.255.253.52/library-backups /mnt/Storage/Files/library-backups \
  -o credentials=/etc/smb-credentials/library-backups.cred,iocharset=utf8,uid=0,gid=0,file_mode=0644,dir_mode=0755,vers=3.0
```

Verify mount:

```bash
findmnt /mnt/Storage/Files/library-backups
df -hT /mnt/Storage/Files/library-backups
```

You should see filesystem type `cifs`.

#### 2. Make mount persistent across reboot

Add this line to `/etc/fstab`:

```fstab
//10.255.253.52/library-backups /mnt/Storage/Files/library-backups cifs credentials=/etc/smb-credentials/library-backups.cred,iocharset=utf8,uid=0,gid=0,file_mode=0644,dir_mode=0755,vers=3.0,_netdev,nofail,x-systemd.automount 0 0
```

Then test:

```bash
sudo mount -a
findmnt /mnt/Storage/Files/library-backups
```

#### 3. Container Volume Mount

Mount the SMB share to the container:

```bash
docker run -d \
  --name library-ms \
  -p 8000:8000 \
  -v /path/to/mounted/smb/share:/mnt/backups \
  -v library-data:/app/data \
  sachinaeroconnections/library-ms:latest
```

#### 4. Configure in App Settings

| Field | Value |
|-------|-------|
| Mount Type | `smb` |
| Mount Path | `/mnt/backups` |
| SMB Server | `//netstorage.local` |
| SMB Username | Your SMB username |
| SMB Password | Your SMB password |
| SMB Domain | WORKGROUP (or your domain) |

Use the **Validate SMB/NFS** button in Settings before running backup.

#### 5. Container Volume Mount

Bind the host-mounted SMB share into the container:

```yaml
volumes:
  - /path/to/mounted/smb/share:/mnt/backups
```

Or with `docker run`:

```bash
docker run -d \
  --name library-ms \
  -p 8000:8000 \
  -v /path/to/mounted/smb/share:/mnt/backups \
  -v library-data:/app/data \
  sachinaeroconnections/library-ms:latest
```

#### Optional: In-container SMB mount

Only use this if your runtime explicitly supports privileged mount capabilities. Set:

```bash
ALLOW_IN_CONTAINER_SMB_MOUNT=true
```

If not enabled, the app will show guidance to use host-mounted SMB paths.

### Backup Storage

Backups are stored as `.tar.gz` files containing:
- SQLite database
- Media files (if any)

Access backup management at `/settings/backups/`

### Celery Beat

For automatic daily backups, ensure Celery Beat is running:

```bash
docker exec -it library-ms celery -A config beat -l INFO
```

## Webhooks

### Notification Webhook

For loan alerts (overdue, due soon):

- Configure in Settings → Notification Webhook
- Supports Slack, Discord, Google Chat, and custom webhooks

### System Alert Webhook

For backup status and system events (separate from notifications):

- Configure in Settings → System Alerts
- Receives backup success/failure notifications
- Alerts when backup mount is unavailable

## Troubleshooting

### CSRF Verification Failed (403 Error)

If you see a `403 Forbidden - CSRF verification failed` error when accessing the application from a domain other than localhost, you need to add your domain to `CSRF_TRUSTED_ORIGINS`.

**Option 1: Quick Fix with Environment Variable**

```bash
docker stop library-ms
docker rm library-ms
docker run -d \
  --name library-ms \
  -e "CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://your-domain.com" \
  -p 8000:8000 \
  -v library-data:/app/data \
  sachinaeroconnections/library-ms:latest
```

**Option 2: Update Domain in Database (Recommended)**

```bash
docker exec -it library-ms python manage.py shell
```

```python
from apps.setup.models import SetupConfig
c = SetupConfig.objects.first()
c.domain = 'https://your-domain.com'
c.save()
```

### View Current CSRF Trusted Origins

```bash
docker exec -it library-ms python manage.py shell -c "from django.conf import settings; print('Trusted origins:', settings.CSRF_TRUSTED_ORIGINS)"
```

### Reset Setup Configuration

```bash
docker exec -it library-ms python manage.py shell -c "
from apps.setup.models import SetupConfig
SetupConfig.objects.all().delete()
print('Setup configuration deleted. Access /setup/ to reconfigure.')
"
```

## Management Commands

| Command | Description |
|---------|-------------|
| `clear_all_data` | Clear all data from database (requires confirmation) |
| `populate_test_data` | Add sample books, borrowers, and loans |
| `remove_test_data` | Remove all test data (with confirmation) |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5 |
| Frontend | TailwindCSS |
| Database | SQLite |
| Container | Docker (Alpine-based) |
| Task Queue | Celery + Redis |
| Notifications | Webhooks, Email |

## Project Structure

```
library-ms/
├── apps/
│   ├── books/              # Book & copy management
│   ├── borrowers/          # Borrower management
│   ├── loans/             # Loan tracking & returns
│   ├── notifications/      # Settings, backup, branding
│   └── setup/            # Setup wizard & configuration
├── config/                 # Django settings
├── templates/              # HTML templates
├── static/                 # CSS, JS
├── media/                  # Uploaded images
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Loan System

| Days Out | Status | Color |
|----------|--------|-------|
| 0-24 | Active | Gray |
| 25-29 | Due Soon | Amber |
| 30+ | Overdue | Red |

## Current App Status (v1.3.9)

- Stable release for production use with Docker and SQLite persistence.
- Session security includes auto logout (10-minute idle timeout, 60-minute absolute timeout).
- Backup management supports local, NFS, and SMB host-mounted paths.
- Pagination is standardized to 10 rows per page for core list views.
- Superadmin-only destructive actions include borrower permanent deletion with safety checks.

## Known Issues

- Some administrative and configuration flows are intentionally restricted to superadmins and may appear unavailable to standard users.
- Borrower historical records in loans/return notes are snapshot-based by borrower name, not relational foreign keys.
- Celery worker/beat services are optional and require separate runtime setup if scheduled tasks are needed continuously.
- In constrained container environments, SMB mounts inside the container may fail unless host-mounted SMB paths are used.

## Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to fitness for a particular purpose and noninfringement.

The operators of this system are responsible for:
- secure secret management and environment configuration,
- backup and recovery procedures,
- access control and compliance with their local policies and legal requirements.

## Third-Party Credits

This project uses and appreciates the following open-source software and assets:

- [Django](https://www.djangoproject.com/) - web framework
- [Django REST Framework](https://www.django-rest-framework.org/) - API toolkit
- [django-allauth](https://github.com/pennersr/django-allauth) - authentication/account management
- [django-filter](https://github.com/carltongibson/django-filter) - filtering support
- [django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms) and [crispy-tailwind](https://github.com/django-crispy-forms/crispy-tailwind) - form rendering
- [Tailwind CSS](https://tailwindcss.com/) (via CDN in current templates) - UI styling
- [Gunicorn](https://gunicorn.org/) - WSGI server
- [Celery](https://docs.celeryq.dev/) and [Redis](https://redis.io/) - background task processing
- [WhiteNoise](https://whitenoise.readthedocs.io/) - static file serving
- [Pillow](https://python-pillow.org/) - image handling
- [Requests](https://requests.readthedocs.io/) - HTTP client utilities
- [PostgreSQL](https://www.postgresql.org/) client libraries (`psycopg2-binary`) for supported external DB deployments

Inline SVG icons in templates are based on common open-source icon patterns (Heroicons-style paths) embedded directly in project templates.

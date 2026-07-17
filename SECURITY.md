# Security Policy

## Scope

This is an internal library management tool designed for private networks. It is not intended to be exposed to the public internet.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.4.x   | :white_check_mark: |
| 1.3.x   | :white_check_mark: |
| < 1.3   | :x:                |

## Reporting a Vulnerability

1. **Do NOT** create a public GitHub issue for security vulnerabilities.
2. Email the maintainer at the address listed in the repository.
3. Include a description, steps to reproduce, and potential impact.
4. Expected response: 48 hours (acknowledgment), 7 days (initial fix).

## Architecture

```
Docker Container (port 8000) → Tailscale Services → Private Network
```

- The application runs inside a Docker container.
- Tailscale Services provides HTTPS and routes traffic within your private network.
- No port forwarding or public internet exposure required.

## Security Layers

### Network Access

- Access is restricted to members of your private network.
- Tailscale ACLs control which users and devices can access the application.
- No exposure to the public internet.

### Application Security

- Session-based authentication via django-allauth
- Server-enforced session timeouts (idle: 10 minutes, absolute: 60 minutes)
- PIN protection for administrative setup pages

### Container Security

- Multi-stage Dockerfile reduces attack surface
- No compilers or unnecessary tools in production image
- Health check endpoint for container monitoring

### Data Protection

- SQLite database stored in persistent Docker volume (`/app/data/`)
- Automatic daily backups to SMB/NFS storage
- Backup files are .tar.gz archives containing database and media

## Access Control

### Tailscale Configuration

Restrict access using Tailscale ACLs. Example:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:library-staff"],
      "dst": ["tag:library-host:443"]
    }
  ]
}
```

### Application Access

- Users must have a valid account on the application.
- Sessions expire automatically (idle + absolute timeout).
- PIN required for administrative setup access.

## Backup and Recovery

Backups are the most critical security measure for this application.

### Configuration

1. Go to **Settings** → **Backup**
2. Enable Auto-Backup
3. Configure backup time and retention period
4. Choose storage: **Local** or **SMB/NFS** (recommended: SMB/NFS)

### Backup Checklist

- [ ] Verify backups are being created automatically
- [ ] Test restoring a backup to a test environment
- [ ] Store at least one backup on external storage
- [ ] Configure system alert webhook for backup failures
- [ ] Verify SMB/NFS mount is reachable before backup runs

### SMB Credentials

If using SMB storage, credentials are stored in a file on your host system:

```bash
sudo chmod 600 /path/to/credentials/file
```

## Environment Configuration

### Required (Production)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (generate a strong, unique value) |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Hostnames the app responds to |

### Recommended

| Variable | Description |
|----------|-------------|
| `CSRF_TRUSTED_ORIGINS` | HTTPS origins for CSRF protection |

## What This Application Is Not

Given its internal, private-network design:

- **Not a public-facing application** — do not expose to the internet
- **Not multi-tenant** — single organization use case
- **Not high-security** — designed for low-threat, trusted environments

## Updating

Keep the application updated by pulling the latest image periodically:

```bash
docker pull sachinaeroconnections/library-ms:latest
docker compose up -d
```

Watch GitHub releases to be notified of updates.

## Known Limitations

- Loan history uses borrower name snapshots rather than relational references. Avoid renaming borrowers with active loan history.
- Session timeouts are enforced server-side. Ensure the server clock is synchronized.
- SMB mounts require host-mounted paths in containerized environments.

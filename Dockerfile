FROM python:3.12-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libpq-dev \
    postgresql-dev \
    python3 \
    py3-pip \
    nodejs \
    npm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN npm install --save-dev tailwindcss@3 && \
    ./node_modules/.bin/tailwindcss -i ./static/src/tailwind.css -o ./static/tailwind.min.css --minify
RUN mkdir -p /app/data && python manage.py migrate

RUN python manage.py collectstatic --noinput || true

FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# REQUIRED: set ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS via environment variables or .env file
# Example: ALLOWED_HOSTS=library.yourdomain.com

WORKDIR /app

RUN apk add --no-cache \
    cifs-utils \
    bash \
    wget \
    python3 \
    py3-pip

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]

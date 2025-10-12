# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=on
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App
COPY . /app

# Collect static (if any) at build time (optional)
RUN python -m compileall -q /app

ENV DJANGO_SETTINGS_MODULE=portalopenwisp.settings
ENV PORT=8000
EXPOSE 8000

# Healthcheck expects /healthz route
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${PORT}/healthz || exit 1

CMD ["gunicorn", "portalopenwisp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

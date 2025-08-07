# --- Stage 1: The Builder ---
FROM python:3.13 AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Stage 2: The Final Production Image ---
FROM python:3.13-slim

# Explicitly set the python path. This is a robust way to ensure Python finds your code.
ENV PYTHONPATH=/app

USER root
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
WORKDIR /app
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
COPY initial_data.json . 
RUN python manage.py collectstatic --no-input
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000

# Final, correct CMD line
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "auth.wsgi:application"]

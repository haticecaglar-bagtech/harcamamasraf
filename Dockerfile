# Backend: Flask (Gunicorn) — production
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg2-binary icin (libpq)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/docker/entrypoint.sh"]

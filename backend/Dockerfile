# Pinned by digest (python:3.12-slim as of 2026-08-18) rather than a
# floating tag, so a build can't silently pull in a different base image
# later. Bump deliberately: `docker pull python:3.12-slim` then update the
# digest below.
FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app

USER appuser

ENV FLASK_APP=wsgi.py
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["./entrypoint.sh"]

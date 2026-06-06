# Backend image for Koyeb / any container host.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install deps first for better layer caching.
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# App source.
COPY . .

# Koyeb (and most hosts) inject $PORT; default to 8000 locally.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

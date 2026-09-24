FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=80

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . /app/

# Run database migrations and collect static files
RUN python manage.py migrate --no-input || true
RUN python manage.py collectstatic --no-input || true

EXPOSE 8080 80 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn mechanic_backend.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120"]

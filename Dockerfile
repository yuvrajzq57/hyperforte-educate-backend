# Build stage
FROM python:3.9-slim as builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Final stage
FROM python:3.9-slim

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8000

WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    # Create app user
    useradd -m -s /bin/bash app && \
    chown -R app:app $APP_HOME

# Copy wheels and install dependencies
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy project files
COPY . $APP_HOME/

# Collect static files
RUN python manage.py collectstatic --noinput
RUN python manage.py makemigrations
RUN python manage.py migrate --noinput

# Change ownership
RUN chown -R app:app $APP_HOME

# Switch to non-root user
USER app

# Expose port
EXPOSE $PORT

# Start gunicorn
CMD gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2
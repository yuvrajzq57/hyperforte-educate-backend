# --- Build stage ---
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio

# Copy and build wheels
COPY requirements.txt .
RUN mkdir wheels \
 && pip wheel --wheel-dir=wheels -r requirements.txt

# --- Final stage ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8000

WORKDIR $APP_HOME

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copy app code
COPY . .

# Create and switch to app user
RUN useradd -m -s /bin/bash app && \
    chown -R app:app $APP_HOME
USER app

EXPOSE $PORT

CMD gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2

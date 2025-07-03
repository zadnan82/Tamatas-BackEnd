FROM python:3.11-slim

# Create non-root user and directory structure
RUN mkdir -p /app && \
    adduser --disabled-password --gecos "" appuser && \
    chown appuser:appuser /app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Environment configuration
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8001  

# Note: The actual command is now specified in docker-compose.yml
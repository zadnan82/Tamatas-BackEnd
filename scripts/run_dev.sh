#!/bin/bash

# Development startup script
echo "Starting Fresh Trade development environment..."

# Start PostgreSQL and Redis (if using Docker)
echo "Starting database and Redis..."
docker-compose up -d db redis

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Initialize sample data
echo "Creating sample data..."
python scripts/init_db.py

# Start the application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
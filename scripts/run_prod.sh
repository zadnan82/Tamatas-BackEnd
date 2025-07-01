
#!/bin/bash

# Production startup script
echo "Starting Fresh Trade production environment..."

# Start all services
docker-compose up -d

echo "All services started!"
echo "API available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"

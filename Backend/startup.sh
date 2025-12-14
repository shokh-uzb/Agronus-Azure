#!/bin/bash
# Azure App Service startup script for Agronus Backend
# Use PORT environment variable provided by Azure, default to 8000 if not set

# Exit on error
set -e

# Log startup
echo "Starting Agronus Backend on port ${PORT:-8000}"

# Start Gunicorn
gunicorn --bind=0.0.0.0:${PORT:-8000} --timeout 600 --workers 2 --threads 2 --access-logfile - --error-logfile - app:app

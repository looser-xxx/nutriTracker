#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Path to the database file
DB_FILE="/app/instance/database.db"

# Check if the database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "Database not found. Initializing..."
    python init_db.py
    echo "Uploading initial food data..."
    python uploadDatabase.py
else
    echo "Database already exists. Skipping initialization."
fi

# Run any pending migrations (if needed)
# python migrate_db.py

echo "Starting NutriTracker server on port 5050..."
# Start Gunicorn with gevent worker
exec gunicorn -k gevent -w 4 -b 0.0.0.0:5050 "app:createApp()"

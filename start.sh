#!/usr/bin/env bash

# 1. Database Initialization
# Run the Python code to create the database tables (db.create_all())
# We use the full path to python and gunicorn for reliability on Render.
echo "Creating database tables via Flask app context..."
python -c "from app import create_app; app = create_app(); with app.app_context(): from app import db; db.create_all()"

# Check if the database creation was successful
if [ $? -ne 0 ]; then
    echo "Database initialization FAILED."
    exit 1
fi

# 2. Start Gunicorn Web Server
echo "Starting Gunicorn server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT
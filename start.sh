#!/usr/bin/env bash

# 1. Database Initialization
echo "Running database setup script (db_setup.py)..."
# Call the dedicated Python script to initialize the DB schema
python db_setup.py

# Check if the database creation was successful
if [ $? -ne 0 ]; then
    echo "Database initialization FAILED. Exiting deployment."
    exit 1
fi

# 2. Start Gunicorn Web Server
echo "Starting Gunicorn server..."
# The 'exec' command replaces the shell process with Gunicorn, which is efficient.
exec gunicorn app:app --bind 0.0.0.0:$PORT
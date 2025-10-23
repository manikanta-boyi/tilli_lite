# db_setup.py - Dedicated script for running database creation on deploy
import os
from app import create_app, db # Assuming create_app and db are imported/defined in app.py

# Create the application
app = create_app()

# Initialize the database within the application context
with app.app_context():
    # This will create the instance folder and the tilli_lite.db file
    # then create all tables based on your models.
    db.create_all()

    # Optional: Run initial data setup if you have a function for that (e.g., setup_demo_data())
    # from app import setup_demo_data
    # setup_demo_data()

print("Database setup complete.")
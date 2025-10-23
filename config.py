import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tilli_lite.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Set up the application ID for Firestore (Mandatory for deployment environment)
    APP_ID = 'tilli-lite-portfolio'
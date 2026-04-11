"""
WSGI configuration for SmartCaisse on PythonAnywhere
"""
import sys
import os

# Add your project directory to the Python path
project_home = '/home/eguidi/smartCaisse'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment for production
os.environ['FLASK_ENV'] = 'production'

# Load environment variables from .env file if it exists
env_file = os.path.join(project_home, '.env')
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Create and configure the Flask app
from app import create_app

app = create_app()

# Optional: Add logging
import logging
logging.basicConfig(stream=sys.stderr)

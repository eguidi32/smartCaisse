"""
Configuration de l'application SmartCaisse
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Chemin de base du projet
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration principale de l'application"""

    # Clé secrète pour les sessions et CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Configuration SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'smartcaisse.db')

    # Désactiver le suivi des modifications (performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration Email (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Durée de validité du token de réinitialisation (en secondes)
    RESET_TOKEN_EXPIRES = 3600  # 1 heure

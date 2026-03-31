"""
Configuration de l'application SmartCaisse
"""
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Chemin de base du projet
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration principale de l'application"""

    # ============================================
    # SÉCURITÉ
    # ============================================
    
    # Clé secrète pour les sessions et CSRF
    # ⚠️ DOIT être définie dans .env en production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Mode Flask
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'

    # ============================================
    # BASE DE DONNÉES
    # ============================================
    
    # Configuration SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'smartcaisse.db')

    # Désactiver le suivi des modifications (performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ============================================
    # EMAIL (Flask-Mail)
    # ============================================
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Durée de validité du token de réinitialisation (en secondes)
    RESET_TOKEN_EXPIRES = 3600  # 1 heure

    # ============================================
    # LOGGING
    # ============================================
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/smartcaisse.log'
    
    @staticmethod
    def get_log_level():
        """Convertit string LOG_LEVEL en constante logging"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(Config.LOG_LEVEL.upper(), logging.INFO)

    # ============================================
    # RATE LIMITING
    # ============================================
    
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"  # En prod, utiliser Redis
    RATELIMIT_STRATEGY = "fixed-window"
    
    # ============================================
    # SÉCURITÉ PRODUCTION
    # ============================================
    
    # HTTPS enforcement (seulement en production)
    FORCE_HTTPS = os.environ.get('FLASK_ENV') == 'production'
    
    # Session sécurisée
    SESSION_COOKIE_SECURE = FORCE_HTTPS  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # Pas accessible via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protection CSRF
    
    # Durée session (30 jours)
    PERMANENT_SESSION_LIFETIME = 2592000

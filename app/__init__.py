"""
Initialisation de l'application SmartCaisse
- Configuration de Flask
- Initialisation des extensions (SQLAlchemy, Login, CSRF, Mail, Talisman, Limiter)
- Configuration du logging
- Enregistrement des Blueprints
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
try:
    from flask_talisman import Talisman
    TALISMAN_AVAILABLE = True
except ImportError:
    TALISMAN_AVAILABLE = False

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None
from config import Config

# Initialisation des extensions (sans app pour le pattern factory)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Rate limiter (optional - graceful degradation if not available)
if LIMITER_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
else:
    limiter = None

# Configuration de Flask-Login
login_manager.login_view = 'auth.login'  # Route de redirection si non connecté
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'


def setup_logging(app):
    """
    Configure le logging de l'application
    - RotatingFileHandler pour les logs en production
    - Console handler pour le développement
    """
    # Créer le dossier logs s'il n'existe pas
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configuration du niveau de log
    log_level = Config.get_log_level()
    
    # Format des logs
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Handler fichier (production)
    if not app.debug:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
    
    # Handler console (toujours actif)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # Définir le niveau global
    app.logger.setLevel(log_level)
    
    app.logger.info('SmartCaisse startup')


def create_app(config_class=Config):
    """
    Factory pattern pour créer l'application Flask

    Args:
        config_class: Classe de configuration à utiliser

    Returns:
        Application Flask configurée
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configuration du logging
    setup_logging(app)

    # Initialisation des extensions avec l'app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    if LIMITER_AVAILABLE and limiter:
        limiter.init_app(app)

    # Ajouter csrf_token manuellement au contexte de template (fallback Flask-WTF)
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into template context"""
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # HTTPS enforcement en production
    if TALISMAN_AVAILABLE and app.config['FORCE_HTTPS']:
        Talisman(app,
                force_https=True,
                strict_transport_security=True,
                strict_transport_security_max_age=31536000,  # 1 an
                content_security_policy=None)  # Désactivé pour éviter conflits Bootstrap
        app.logger.info('HTTPS enforcement enabled (Talisman)')
    elif app.config['FORCE_HTTPS']:
        app.logger.warning('HTTPS enforcement requested but Talisman not available')

    # Import et enregistrement des Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.transactions import transactions_bp
    from app.routes.reports import reports_bp
    from app.routes.debts import debts_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp
    from app.routes.inventory import inventory_bp
    from app.routes.invoices import bp as invoices_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(debts_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(invoices_bp)

    # Création des tables si elles n'existent pas
    with app.app_context():
        # Only create tables if they don't exist (check for a key table)
        # This prevents unnecessary recreations on every app startup
        try:
            from app.models import AuditLog
            # If we can query the table, it exists
            AuditLog.query.first()
            app.logger.info('Database tables already exist')
        except Exception:
            # Tables don't exist, create them
            db.create_all()
            app.logger.info('Database tables created')

    
    # Initialiser le scheduler pour tâches périodiques (désactivé en production PythonAnywhere)
    # PythonAnywhere gère les tâches planifiées via son propre système de tâches
    # if not app.debug and app.config['FLASK_ENV'] == 'production':
    #     try:
    #         from app.scheduler import init_scheduler
    #         init_scheduler(app)
    #     except Exception as e:
    #         app.logger.error(f'Failed to initialize scheduler: {e}')

    return app


@login_manager.user_loader
def load_user(user_id):
    """Callback requis par Flask-Login pour charger un utilisateur"""
    from app.models import User
    return User.query.get(int(user_id))

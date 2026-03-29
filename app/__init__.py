"""
Initialisation de l'application SmartCaisse
- Configuration de Flask
- Initialisation des extensions (SQLAlchemy, Login, CSRF, Mail)
- Enregistrement des Blueprints
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import Config

# Initialisation des extensions (sans app pour le pattern factory)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Configuration de Flask-Login
login_manager.login_view = 'auth.login'  # Route de redirection si non connecté
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'


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

    # Initialisation des extensions avec l'app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Import et enregistrement des Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.transactions import transactions_bp
    from app.routes.reports import reports_bp
    from app.routes.debts import debts_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(debts_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)

    # Création des tables si elles n'existent pas
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    """Callback requis par Flask-Login pour charger un utilisateur"""
    from app.models import User
    return User.query.get(int(user_id))

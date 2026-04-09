"""
Utilitaires pour SmartCaisse
- Audit logging
- Helpers généraux
"""
from functools import wraps
from flask import request, current_app
from flask_login import current_user
from app import db


def log_audit(action, entity_type, entity_id=None, old_value=None, new_value=None, reason=None, status='success'):
    """
    Enregistre une action critique dans l'audit log

    Args:
        action: Type d'action (create, update, delete, login, logout, reset_password)
        entity_type: Type d'entité (User, Transaction, Debt, Payment, Product, Invoice)
        entity_id: ID de l'entité modifiée (optionnel)
        old_value: Ancienne valeur pour les updates (optionnel)
        new_value: Nouvelle valeur pour les updates (optionnel)
        reason: Notes ou raison de l'erreur (optionnel)
        status: 'success' ou 'error' (défaut: success)
    """
    from app.models import AuditLog

    try:
        # Capturer le contexte de la requête
        ip_address = request.remote_addr if request else None
        method = request.method if request else None
        endpoint = request.endpoint if request else None
        user_id = current_user.id if current_user and current_user.is_authenticated else None

        # Limiter la taille des valeurs
        old_value_str = str(old_value)[:500] if old_value else None
        new_value_str = str(new_value)[:500] if new_value else None

        # Créer le log d'audit
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value_str,
            new_value=new_value_str,
            ip_address=ip_address,
            method=method,
            endpoint=endpoint,
            status=status,
            reason=reason
        )

        db.session.add(audit_log)
        db.session.commit()

        return True
    except Exception as e:
        # Ne pas lever d'exception - juste logger l'erreur
        current_app.logger.error(f'Erreur lors de l\'enregistrement du log d\'audit: {str(e)}')
        return False


def audit_action(action, entity_type):
    """
    Décorateur pour logger automatiquement les actions

    Usage:
        @audit_action('create', 'User')
        def add_user():
            ...

    Les erreurs sont automatiquement loggées comme 'error' status
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                log_audit(action, entity_type, status='success')
                return result
            except Exception as e:
                log_audit(action, entity_type, reason=str(e), status='error')
                raise
        return decorated_function
    return decorator

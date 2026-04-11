"""
Routes pour l'administration
- Dashboard admin
- Gestion des utilisateurs (CRUD)
- Statistiques globales
"""
from functools import wraps
import secrets
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify, send_file
from flask_login import login_required, current_user
from flask_mail import Message
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db, mail
from app.models import User, Transaction, Client, Dette, Paiement, AuditLog
from app.utils import log_audit

# Création du Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def generate_temp_password(length=8):
    """Génère un mot de passe temporaire aléatoire"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_welcome_email(user, temp_password):
    """Envoie l'email de bienvenue avec les identifiants"""
    login_url = url_for('auth.login', _external=True)

    # Mode développement: si pas de configuration email, afficher dans la console
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 60)
        print('MODE DEVELOPPEMENT - Email de bienvenue:')
        print(f'Destinataire: {user.email}')
        print(f'Nom d\'utilisateur: {user.username}')
        print(f'Mot de passe temporaire: {temp_password}')
        print(f'Lien de connexion: {login_url}')
        print('=' * 60 + '\n')
        return True

    msg = Message(
        subject='SmartCaisse - Votre compte a été créé',
        recipients=[user.email]
    )

    msg.body = f'''Bonjour {user.username},

Votre compte SmartCaisse a été créé avec succès !

Voici vos identifiants de connexion :
- Email : {user.email}
- Mot de passe temporaire : {temp_password}

Connectez-vous ici : {login_url}

IMPORTANT : Pour des raisons de sécurité, vous devrez changer votre mot de passe lors de votre première connexion.

Cordialement,
L'équipe SmartCaisse
'''

    msg.html = f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0d6efd;">
            <span style="margin-right: 10px;">💰</span>SmartCaisse
        </h2>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Votre compte SmartCaisse a été créé avec succès !</p>

        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #495057;">Vos identifiants de connexion</h3>
            <p><strong>Email :</strong> {user.email}</p>
            <p><strong>Mot de passe temporaire :</strong>
                <code style="background-color: #e9ecef; padding: 4px 8px; border-radius: 4px; font-size: 14px;">
                    {temp_password}
                </code>
            </p>
        </div>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{login_url}"
               style="background-color: #0d6efd; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Se connecter
            </a>
        </p>

        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
            <strong>⚠️ Important :</strong> Pour des raisons de sécurité, vous devrez changer votre mot de passe lors de votre première connexion.
        </div>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            Cet email a été envoyé automatiquement. Si vous n'êtes pas à l'origine de cette demande, veuillez contacter un administrateur.
        </p>
    </div>
</body>
</html>
'''

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erreur envoi email de bienvenue: {e}')
        return False


def send_password_reset_email(user, temp_password):
    """Envoie l'email de réinitialisation du mot de passe par admin"""
    login_url = url_for('auth.login', _external=True)

    # Mode développement: si pas de configuration email, afficher dans la console
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 60)
        print('MODE DEVELOPPEMENT - Réinitialisation mot de passe:')
        print(f'Destinataire: {user.email}')
        print(f'Nouveau mot de passe temporaire: {temp_password}')
        print(f'Lien de connexion: {login_url}')
        print('=' * 60 + '\n')
        return True

    msg = Message(
        subject='SmartCaisse - Votre mot de passe a été réinitialisé',
        recipients=[user.email]
    )

    msg.body = f'''Bonjour {user.username},

Votre mot de passe SmartCaisse a été réinitialisé par un administrateur.

Voici votre nouveau mot de passe temporaire : {temp_password}

Connectez-vous ici : {login_url}

IMPORTANT : Pour des raisons de sécurité, vous devrez changer votre mot de passe lors de votre prochaine connexion.

Cordialement,
L'équipe SmartCaisse
'''

    msg.html = f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0d6efd;">
            <span style="margin-right: 10px;">💰</span>SmartCaisse
        </h2>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Votre mot de passe a été réinitialisé par un administrateur.</p>

        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #495057;">Nouveau mot de passe</h3>
            <p><strong>Mot de passe temporaire :</strong>
                <code style="background-color: #e9ecef; padding: 4px 8px; border-radius: 4px; font-size: 14px;">
                    {temp_password}
                </code>
            </p>
        </div>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{login_url}"
               style="background-color: #0d6efd; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Se connecter
            </a>
        </p>

        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
            <strong>⚠️ Important :</strong> Vous devrez changer ce mot de passe lors de votre prochaine connexion.
        </div>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            Si vous n'avez pas demandé cette réinitialisation, veuillez contacter un administrateur immédiatement.
        </p>
    </div>
</body>
</html>
'''

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erreur envoi email réinitialisation: {e}')
        return False


# ============================================
# DASHBOARD ADMIN
# ============================================

@admin_bp.route('/')
@admin_required
def dashboard():
    """Dashboard administrateur avec statistiques globales"""
    # Statistiques utilisateurs
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(role='admin').count()

    # Derniers utilisateurs inscrits
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # Statistiques globales des transactions
    total_recettes = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'recette'
    ).scalar() or 0

    total_depenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'depense'
    ).scalar() or 0

    # Statistiques des dettes
    total_dettes = db.session.query(func.sum(Dette.montant_dette)).scalar() or 0

    # Total clients
    total_clients = Client.query.count()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           admin_users=admin_users,
                           recent_users=recent_users,
                           total_recettes=total_recettes,
                           total_depenses=total_depenses,
                           total_dettes=total_dettes,
                           total_clients=total_clients)


# ============================================
# AUDIT LOGS
# ============================================

@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    """Liste des audit logs avec filtrage et recherche"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    user_filter = request.args.get('user', None, type=int)
    status_filter = request.args.get('status', '')

    query = AuditLog.query

    # Appliquer les filtres
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    if entity_filter:
        query = query.filter(AuditLog.entity_type == entity_filter)

    if user_filter:
        query = query.filter(AuditLog.user_id == user_filter)

    if status_filter in ['success', 'error']:
        query = query.filter(AuditLog.status == status_filter)

    # Pagination et tri
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Récupérer les filtres disponibles pour les dropdowns
    all_actions = db.session.query(AuditLog.action).distinct().order_by(AuditLog.action).all()
    all_actions = [a[0] for a in all_actions]

    all_entities = db.session.query(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type).all()
    all_entities = [e[0] for e in all_entities]

    all_users = User.query.order_by(User.username).all()

    return render_template('admin/audit_logs.html',
                           pagination=pagination,
                           logs=pagination.items,
                           action_filter=action_filter,
                           entity_filter=entity_filter,
                           user_filter=user_filter,
                           status_filter=status_filter,
                           all_actions=all_actions,
                           all_entities=all_entities,
                           all_users=all_users)


# ============================================
# ANALYTICS & REPORTING
# ============================================

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Dashboard avec analytics et charts"""
    # Récupérer les données pour les 30 derniers jours
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Stats générales
    total_users = User.query.count()
    recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()

    # Stats transactions
    total_transactions = Transaction.query.count()
    total_recettes = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'recette'
    ).scalar() or 0
    total_depenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'depense'
    ).scalar() or 0

    # Stats audit
    total_audit_logs = AuditLog.query.count()
    recent_audit_logs = AuditLog.query.filter(AuditLog.timestamp >= thirty_days_ago).count()

    return render_template('admin/analytics.html',
                           total_users=total_users,
                           recent_users=recent_users,
                           total_transactions=total_transactions,
                           total_recettes=total_recettes,
                           total_depenses=total_depenses,
                           total_audit_logs=total_audit_logs,
                           recent_audit_logs=recent_audit_logs)


@admin_bp.route('/analytics/api/transactions')
@admin_required
def analytics_transactions():
    """API pour données des charts de transactions"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Grouper par jour
    transactions = db.session.query(
        func.date(Transaction.date).label('date'),
        Transaction.type,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).filter(Transaction.date >= start_date).group_by(
        func.date(Transaction.date),
        Transaction.type
    ).order_by(func.date(Transaction.date)).all()

    # Formater les données
    dates = {}
    for transaction in transactions:
        date_str = transaction.date.strftime('%Y-%m-%d')
        if date_str not in dates:
            dates[date_str] = {'recette': 0, 'depense': 0, 'count_recette': 0, 'count_depense': 0}

        if transaction.type == 'recette':
            dates[date_str]['recette'] = float(transaction.total or 0)
            dates[date_str]['count_recette'] = transaction.count
        else:
            dates[date_str]['depense'] = float(transaction.total or 0)
            dates[date_str]['count_depense'] = transaction.count

    return jsonify({
        'dates': sorted(dates.keys()),
        'recettes': [dates[d]['recette'] for d in sorted(dates.keys())],
        'depenses': [dates[d]['depense'] for d in sorted(dates.keys())],
        'count_recettes': [dates[d]['count_recette'] for d in sorted(dates.keys())],
        'count_depenses': [dates[d]['count_depense'] for d in sorted(dates.keys())]
    })


@admin_bp.route('/analytics/api/users')
@admin_required
def analytics_users():
    """API pour données des charts d'utilisateurs"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Grouper par jour
    users = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= start_date).group_by(
        func.date(User.created_at)
    ).order_by(func.date(User.created_at)).all()

    # Formater les données
    dates = {}
    cumulative = 0
    for user in users:
        date_str = user.date.strftime('%Y-%m-%d')
        cumulative += user.count
        dates[date_str] = {'new': user.count, 'total': cumulative}

    return jsonify({
        'dates': sorted(dates.keys()),
        'new_users': [dates[d]['new'] for d in sorted(dates.keys())],
        'total_users': [dates[d]['total'] for d in sorted(dates.keys())]
    })


@admin_bp.route('/analytics/api/audit-actions')
@admin_required
def analytics_audit_actions():
    """API pour distribution des actions d'audit"""
    action_counts = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).all()

    return jsonify({
        'actions': [a[0] for a in action_counts],
        'counts': [a[1] for a in action_counts]
    })


@admin_bp.route('/user/<int:id>/activity')
@admin_required
def user_activity(id):
    """Rapport d'activité d'un utilisateur"""
    user = User.query.get_or_404(id)

    # Récupérer les audit logs de cet utilisateur
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.filter_by(user_id=id).order_by(
        AuditLog.timestamp.desc()
    ).paginate(page=page, per_page=20, error_out=False)

    # Stats d'activité
    total_actions = AuditLog.query.filter_by(user_id=id).count()
    recent_actions = AuditLog.query.filter_by(user_id=id).filter(
        AuditLog.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()

    # Actions par type
    action_distribution = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter_by(user_id=id).group_by(AuditLog.action).order_by(
        func.count(AuditLog.id).desc()
    ).all()

    return render_template('admin/user_activity.html',
                           user=user,
                           pagination=logs,
                           logs=logs.items,
                           total_actions=total_actions,
                           recent_actions=recent_actions,
                           action_distribution=action_distribution)


@admin_bp.route('/audit-logs/export/csv')
@admin_required
def export_audit_logs_csv():
    """Exporter les audit logs en CSV"""
    import csv
    from io import StringIO

    # Récupérer tous les audit logs
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()

    # Générer le CSV de manière sécurisée
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Utilisateur', 'Action', 'Entité', 'ID', 'IP', 'Méthode', 'Endpoint', 'Statut', 'Raison', 'Nouvelle Valeur'])

    for log in logs:
        username = log.user.username if log.user else "System"
        timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([
            timestamp,
            username,
            log.action,
            log.entity_type,
            log.entity_id or '',
            log.ip_address or '',
            log.method or '',
            log.endpoint or '',
            log.status,
            log.reason or '',
            log.new_value or ''
        ])

    csv_content = output.getvalue()

    from flask import Response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )


@admin_bp.route('/audit-logs/export/pdf')
@admin_required
def export_audit_logs_pdf():
    """Exporter les audit logs en PDF"""
    from app.exports.pdf_generator import PDFGenerator

    # Récupérer les audit logs des 7 derniers jours
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs = AuditLog.query.filter(AuditLog.timestamp >= seven_days_ago).order_by(
        AuditLog.timestamp.desc()
    ).all()

    generator = PDFGenerator("Rapport Audit Logs")
    pdf_buffer = generator.generate_audit_logs_pdf(logs, current_app.config)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.pdf'
    )


# ============================================
# GESTION DES UTILISATEURS
# ============================================

@admin_bp.route('/users')
@admin_required
def list_users():
    """Liste de tous les utilisateurs"""
    search = request.args.get('search', '').strip()
    filter_role = request.args.get('role', '')
    filter_status = request.args.get('status', '')

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    if filter_role in ['admin', 'user']:
        query = query.filter(User.role == filter_role)

    if filter_status == 'active':
        query = query.filter(User.is_active == True)
    elif filter_status == 'inactive':
        query = query.filter(User.is_active == False)

    users = query.order_by(User.created_at.desc()).all()

    return render_template('admin/users.html',
                           users=users,
                           search=search,
                           filter_role=filter_role,
                           filter_status=filter_status)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Créer un nouvel utilisateur"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'user')
        generate_password = request.form.get('generate_password') == 'on'

        errors = []

        # Validations
        if not username or len(username) < 3:
            errors.append('Le nom d\'utilisateur doit avoir au moins 3 caractères.')

        if not email or '@' not in email:
            errors.append('Email invalide.')

        if role not in ['admin', 'user']:
            role = 'user'

        # Vérifier unicité
        if User.query.filter_by(username=username).first():
            errors.append('Ce nom d\'utilisateur existe déjà.')

        if User.query.filter_by(email=email).first():
            errors.append('Cet email existe déjà.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/user_add.html')

        # Générer mot de passe temporaire
        temp_password = generate_temp_password()

        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True,
            must_change_password=True
        )
        user.set_password(temp_password)

        db.session.add(user)
        db.session.commit()

        # Logger l'action
        log_audit('create', 'User', entity_id=user.id, new_value=f'username={username}, role={role}')

        # Envoyer l'email de bienvenue avec les identifiants
        if send_welcome_email(user, temp_password):
            flash(f'Utilisateur "{username}" créé avec succès ! Un email avec les identifiants a été envoyé.', 'success')
        else:
            flash(f'Utilisateur "{username}" créé avec succès !', 'success')
            flash(f'⚠️ Erreur lors de l\'envoi de l\'email. Mot de passe temporaire : {temp_password}', 'warning')

        return redirect(url_for('admin.user_detail', id=user.id))

    return render_template('admin/user_add.html')


@admin_bp.route('/users/<int:id>')
@admin_required
def user_detail(id):
    """Détail d'un utilisateur"""
    user = User.query.get_or_404(id)

    # Statistiques de l'utilisateur
    nb_transactions = user.transactions.count()
    nb_clients = user.clients.count()

    total_recettes = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == 'recette'
    ).scalar() or 0

    total_depenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == 'depense'
    ).scalar() or 0

    return render_template('admin/user_detail.html',
                           user=user,
                           nb_transactions=nb_transactions,
                           nb_clients=nb_clients,
                           total_recettes=total_recettes,
                           total_depenses=total_depenses)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    """Modifier un utilisateur"""
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'user')

        errors = []

        if not username or len(username) < 3:
            errors.append('Le nom d\'utilisateur doit avoir au moins 3 caractères.')

        if not email or '@' not in email:
            errors.append('Email invalide.')

        # Vérifier unicité (sauf pour cet utilisateur)
        existing = User.query.filter(User.username == username, User.id != id).first()
        if existing:
            errors.append('Ce nom d\'utilisateur existe déjà.')

        existing = User.query.filter(User.email == email, User.id != id).first()
        if existing:
            errors.append('Cet email existe déjà.')

        # Empêcher de retirer son propre rôle admin
        if user.id == current_user.id and role != 'admin':
            errors.append('Vous ne pouvez pas retirer votre propre rôle admin.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/user_edit.html', user=user)

        user.username = username
        user.email = email
        user.role = role

        db.session.commit()

        # Logger l'action
        log_audit('update', 'User', entity_id=id, new_value=f'username={username}, role={role}')

        flash('Utilisateur modifié avec succès !', 'success')
        return redirect(url_for('admin.user_detail', id=id))

    return render_template('admin/user_edit.html', user=user)


@admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_user(id):
    """Activer/Désactiver un utilisateur"""
    user = User.query.get_or_404(id)

    # Empêcher de désactiver son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'danger')
        return redirect(url_for('admin.user_detail', id=id))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activé' if user.is_active else 'désactivé'

    # Logger l'action
    log_audit('update', 'User', entity_id=id, new_value=f'is_active={user.is_active}')

    flash(f'Compte de {user.username} {status}.', 'success')
    return redirect(url_for('admin.user_detail', id=id))


@admin_bp.route('/users/<int:id>/reset-password', methods=['POST'])
@admin_required
def reset_password(id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    user = User.query.get_or_404(id)

    # Générer nouveau mot de passe temporaire
    temp_password = generate_temp_password()
    user.set_password(temp_password)
    user.must_change_password = True

    db.session.commit()

    # Logger l'action (CRITICAL - ne pas loguer le nouveau mot de passe)
    log_audit('reset_password', 'User', entity_id=id, reason='Admin password reset')

    # Envoyer l'email avec le nouveau mot de passe
    if send_password_reset_email(user, temp_password):
        flash(f'Mot de passe réinitialisé pour {user.username}. Un email a été envoyé.', 'success')
    else:
        flash(f'Mot de passe réinitialisé pour {user.username}.', 'success')
        flash(f'⚠️ Erreur lors de l\'envoi de l\'email. Nouveau mot de passe temporaire : {temp_password}', 'warning')

    return redirect(url_for('admin.user_detail', id=id))


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(id)

    # Empêcher de supprimer son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.user_detail', id=id))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    # Logger l'action
    log_audit('delete', 'User', entity_id=id, new_value=f'deleted_username={username}')

    flash(f'Utilisateur "{username}" supprimé.', 'info')
    return redirect(url_for('admin.list_users'))

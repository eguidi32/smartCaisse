"""
Routes d'authentification (login, register, logout, reset password)
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from app import db, mail
from app.models import User

# Création du Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription - désactivée, seuls les admins peuvent créer des comptes"""
    flash('L\'inscription publique est désactivée. Contactez un administrateur.', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        # Si doit changer le mot de passe, forcer la redirection
        if current_user.must_change_password:
            return redirect(url_for('profile.change_password'))
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Vérifier si le compte est actif
            if not user.is_active:
                flash('Ce compte a été désactivé. Contactez un administrateur.', 'danger')
                return render_template('auth/login.html')

            # Mettre à jour la date de dernière connexion
            user.last_login = datetime.utcnow()
            db.session.commit()

            login_user(user, remember=bool(remember))
            flash(f'Bienvenue, {user.username} !', 'success')

            # Si doit changer le mot de passe, forcer la redirection
            if user.must_change_password:
                flash('Vous devez changer votre mot de passe.', 'warning')
                return redirect(url_for('profile.change_password'))

            # Rediriger vers la page demandée ou le dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


def send_reset_email(user):
    """Envoie l'email de réinitialisation du mot de passe"""
    token = user.get_reset_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # Mode développement: si pas de configuration email, afficher le lien dans la console
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 60)
        print('MODE DEVELOPPEMENT - Lien de réinitialisation:')
        print(f'Utilisateur: {user.email}')
        print(f'Lien: {reset_url}')
        print('=' * 60 + '\n')
        return True

    msg = Message(
        subject='SmartCaisse - Réinitialisation de votre mot de passe',
        recipients=[user.email]
    )

    msg.body = f'''Bonjour {user.username},

Vous avez demandé la réinitialisation de votre mot de passe SmartCaisse.

Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :
{reset_url}

Ce lien expire dans 1 heure.

Si vous n'avez pas fait cette demande, ignorez simplement cet email.

Cordialement,
L'équipe SmartCaisse
'''

    msg.html = f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0d6efd;">SmartCaisse</h2>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #0d6efd; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Réinitialiser mon mot de passe
            </a>
        </p>
        <p><small>Ou copiez ce lien dans votre navigateur :<br>
        <a href="{reset_url}">{reset_url}</a></small></p>
        <p><strong>Ce lien expire dans 1 heure.</strong></p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            Si vous n'avez pas fait cette demande, ignorez simplement cet email.
        </p>
    </div>
</body>
</html>
'''

    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erreur envoi email: {e}')
        return False


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Page de demande de réinitialisation du mot de passe"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email or '@' not in email:
            flash('Veuillez entrer une adresse email valide.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        # Toujours afficher le même message (sécurité)
        if user and user.is_active:
            if send_reset_email(user):
                flash('Un email de réinitialisation a été envoyé à votre adresse.', 'success')
            else:
                flash('Erreur lors de l\'envoi de l\'email. Veuillez réessayer.', 'danger')
                return render_template('auth/forgot_password.html')
        else:
            # Message identique même si l'utilisateur n'existe pas (sécurité)
            flash('Si cette adresse existe, un email de réinitialisation a été envoyé.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Page de réinitialisation du mot de passe avec token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Vérifier le token
    user = User.verify_reset_token(token)

    if not user:
        flash('Le lien de réinitialisation est invalide ou a expiré.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if len(password) < 6:
            errors.append('Le mot de passe doit contenir au moins 6 caractères.')

        if password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset_password.html', token=token)

        # Mettre à jour le mot de passe
        user.set_password(password)
        user.must_change_password = False
        db.session.commit()

        flash('Votre mot de passe a été réinitialisé avec succès !', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)

"""
Routes pour le profil utilisateur
- Voir son profil
- Modifier son mot de passe
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db

# Création du Blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    """Afficher le profil de l'utilisateur"""
    return render_template('profile/index.html')


@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Changer son mot de passe"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        # Vérifier le mot de passe actuel (sauf si must_change_password)
        if not current_user.must_change_password:
            if not current_user.check_password(current_password):
                errors.append('Mot de passe actuel incorrect.')

        # Valider le nouveau mot de passe
        if len(new_password) < 6:
            errors.append('Le nouveau mot de passe doit avoir au moins 6 caractères.')

        if new_password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('profile/change_password.html')

        # Mettre à jour le mot de passe
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()

        flash('Mot de passe modifié avec succès !', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile/change_password.html')


@profile_bp.route('/company', methods=['GET', 'POST'])
@login_required
def edit_company():
    """Éditer les détails de l'entreprise"""
    if request.method == 'POST':
        current_user.company_name = request.form.get('company_name', '').strip() or None
        current_user.company_address = request.form.get('company_address', '').strip() or None
        current_user.company_phone = request.form.get('company_phone', '').strip() or None
        current_user.company_email = request.form.get('company_email', '').strip() or None
        current_user.company_website = request.form.get('company_website', '').strip() or None
        current_user.company_registration = request.form.get('company_registration', '').strip() or None
        current_user.company_tax_id = request.form.get('company_tax_id', '').strip() or None
        
        db.session.commit()
        flash('Détails de l\'entreprise mis à jour avec succès !', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('profile/edit_company.html')

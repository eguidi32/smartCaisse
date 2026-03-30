"""
Routes pour la gestion des dettes clients
- Clients : liste, ajout
- Dettes : liste par client, ajout
- Paiements : liste par dette, ajout
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Client, Dette, Paiement

# Création du Blueprint
debts_bp = Blueprint('debts', __name__, url_prefix='/debts')


# ============================================
# DASHBOARD DETTES
# ============================================

@debts_bp.route('/')
@login_required
def dashboard():
    """Dashboard des dettes - vue d'ensemble"""
    # Statistiques globales
    clients = Client.query.filter_by(user_id=current_user.id).all()

    total_clients = len(clients)
    total_dette = sum(c.total_dette for c in clients)
    total_paye = sum(c.total_paye for c in clients)
    total_restant = sum(c.total_restant for c in clients)

    # Clients avec dettes actives (triés par montant restant décroissant)
    clients_avec_dettes = [c for c in clients if c.total_restant > 0]
    clients_avec_dettes.sort(key=lambda c: c.total_restant, reverse=True)

    # Derniers paiements
    derniers_paiements = Paiement.query.join(Dette).join(Client).filter(
        Client.user_id == current_user.id
    ).order_by(Paiement.created_at.desc()).limit(5).all()

    return render_template('debts/dashboard.html',
                           total_clients=total_clients,
                           total_dette=total_dette,
                           total_paye=total_paye,
                           total_restant=total_restant,
                           clients_avec_dettes=clients_avec_dettes[:5],
                           derniers_paiements=derniers_paiements)


# ============================================
# GESTION DES CLIENTS
# ============================================

@debts_bp.route('/clients')
@login_required
def list_clients():
    """Liste de tous les clients"""
    search = request.args.get('search', '').strip()

    query = Client.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(
            db.or_(
                Client.nom.ilike(f'%{search}%'),
                Client.telephone.ilike(f'%{search}%')
            )
        )

    clients = query.order_by(Client.nom).all()

    return render_template('debts/clients.html',
                           clients=clients,
                           search=search)


@debts_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    """Ajouter un nouveau client"""
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        email = request.form.get('email', '').strip()
        adresse = request.form.get('adresse', '').strip()

        # Validations
        errors = []

        if not nom:
            errors.append('Le nom est obligatoire.')

        if not telephone:
            errors.append('Le téléphone est obligatoire.')

        # Vérifier unicité du téléphone pour cet utilisateur
        existing = Client.query.filter_by(
            telephone=telephone,
            user_id=current_user.id
        ).first()

        if existing:
            errors.append('Ce numéro de téléphone existe déjà.')

        # Vérifier unicité de l'email pour cet utilisateur (si fourni)
        if email:
            existing_email = Client.query.filter_by(
                email=email,
                user_id=current_user.id
            ).first()
            if existing_email:
                errors.append('Cet email existe déjà pour votre compte.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('debts/client_add.html')

        # Création du client
        client = Client(
            nom=nom,
            telephone=telephone,
            email=email if email else None,
            adresse=adresse,
            user_id=current_user.id
        )

        db.session.add(client)
        db.session.commit()

        # Envoyer email de bienvenue si email fourni
        if client.email:
            from app.email_service import send_client_registration_email
            send_client_registration_email(client)
            flash(f'Client "{nom}" ajouté avec succès ! Email de bienvenue envoyé.', 'success')
        else:
            flash(f'Client "{nom}" ajouté avec succès !', 'success')

        return redirect(url_for('debts.list_clients'))

    return render_template('debts/client_add.html')


@debts_bp.route('/clients/<int:id>')
@login_required
def client_detail(id):
    """Détail d'un client avec ses dettes"""
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Dettes triées par date décroissante
    dettes = client.dettes.order_by(Dette.date.desc()).all()

    return render_template('debts/client_debts.html',
                           client=client,
                           dettes=dettes)


@debts_bp.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    """Modifier un client"""
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        email = request.form.get('email', '').strip()
        adresse = request.form.get('adresse', '').strip()

        errors = []

        if not nom:
            errors.append('Le nom est obligatoire.')

        if not telephone:
            errors.append('Le téléphone est obligatoire.')

        # Vérifier unicité du téléphone (sauf pour ce client)
        existing = Client.query.filter(
            Client.telephone == telephone,
            Client.user_id == current_user.id,
            Client.id != id
        ).first()

        if existing:
            errors.append('Ce numéro de téléphone existe déjà.')

        # Vérifier unicité de l'email (sauf pour ce client)
        if email:
            existing_email = Client.query.filter(
                Client.email == email,
                Client.user_id == current_user.id,
                Client.id != id
            ).first()
            if existing_email:
                errors.append('Cet email existe déjà pour votre compte.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('debts/client_edit.html', client=client)

        # Déterminer si l'email a changé
        email_changed = (email != client.email)

        client.nom = nom
        client.telephone = telephone
        client.adresse = adresse

        # Si l'email change, réinitialiser la confirmation
        if email_changed:
            client.email = email if email else None
            client.email_confirmed = False
            client.email_confirmed_at = None
            client.email_confirmation_token = None
        else:
            client.email = email if email else None

        db.session.commit()

        flash('Client modifié avec succès !', 'success')
        return redirect(url_for('debts.client_detail', id=id))

    return render_template('debts/client_edit.html', client=client)


@debts_bp.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    """Supprimer un client"""
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    nom = client.nom
    db.session.delete(client)
    db.session.commit()

    flash(f'Client "{nom}" supprimé.', 'info')
    return redirect(url_for('debts.list_clients'))


@debts_bp.route('/email-confirmation/<token>')
def confirm_email(token):
    """
    Confirme l'email d'un client (public, pas de login requis)
    Lien de confirmation cliqué par le client
    """
    # Chercher le client avec ce token
    # Il faut parcourir tous les clients car le token contient l'email
    client = None
    from itsdangerous import URLSafeTimedSerializer

    for c in Client.query.all():
        if c.email_confirmation_token == token:
            # Vérifier que le token est valide
            verified_client = Client.verify_email_confirmation_token(token, c.id)
            if verified_client:
                client = verified_client
                break

    if not client:
        flash('Lien de confirmation invalide ou expiré.', 'danger')
        return redirect(url_for('auth.login'))

    # Confirmer l'email
    client.set_email_confirmed()
    db.session.commit()

    flash(f'Email confirmé avec succès ! Vous recevrez désormais les notifications de vos dettes.', 'success')
    return render_template('debts/email_confirmed.html', client=client)



# ============================================
# GESTION DES DETTES
# ============================================

@debts_bp.route('/clients/<int:client_id>/add-debt', methods=['GET', 'POST'])
@login_required
def add_dette(client_id):
    """Ajouter une dette à un client"""
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        montant = request.form.get('montant', '')
        date_str = request.form.get('date', '')

        errors = []

        if not description:
            errors.append('La description est obligatoire.')

        try:
            montant = float(montant)
            if montant <= 0:
                errors.append('Le montant doit être positif.')
        except ValueError:
            errors.append('Montant invalide.')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_obj = datetime.now().date()

        if errors:
            for error in errors:
                flash(error, 'danger')
            today = datetime.now().strftime('%Y-%m-%d')
            return render_template('debts/debt_add.html', client=client, today=today)

        # Création de la dette
        dette = Dette(
            description=description,
            montant_dette=montant,
            date=date_obj,
            client_id=client.id
        )

        db.session.add(dette)
        db.session.commit()

        # Envoyer notification au client si email confirmé
        if client.email and client.email_confirmed:
            from app.email_service import send_debt_notification_email
            send_debt_notification_email(client, dette)

        flash(f'Dette de {montant:.0f} FCFA ajoutée pour {client.nom} !', 'success')
        return redirect(url_for('debts.client_detail', id=client_id))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('debts/debt_add.html', client=client, today=today)


@debts_bp.route('/dette/<int:id>')
@login_required
def dette_detail(id):
    """Détail d'une dette avec ses paiements"""
    dette = Dette.query.join(Client).filter(
        Dette.id == id,
        Client.user_id == current_user.id
    ).first_or_404()

    paiements = dette.paiements.order_by(Paiement.date.desc()).all()

    return render_template('debts/debt_payments.html',
                           dette=dette,
                           paiements=paiements)


@debts_bp.route('/dette/<int:id>/delete', methods=['POST'])
@login_required
def delete_dette(id):
    """Supprimer une dette"""
    dette = Dette.query.join(Client).filter(
        Dette.id == id,
        Client.user_id == current_user.id
    ).first_or_404()

    client_id = dette.client_id
    db.session.delete(dette)
    db.session.commit()

    flash('Dette supprimée.', 'info')
    return redirect(url_for('debts.client_detail', id=client_id))


# ============================================
# GESTION DES PAIEMENTS
# ============================================

@debts_bp.route('/dette/<int:dette_id>/pay', methods=['GET', 'POST'])
@login_required
def add_paiement(dette_id):
    """Ajouter un paiement à une dette"""
    dette = Dette.query.join(Client).filter(
        Dette.id == dette_id,
        Client.user_id == current_user.id
    ).first_or_404()

    if request.method == 'POST':
        montant = request.form.get('montant', '')
        date_str = request.form.get('date', '')

        errors = []

        try:
            montant = float(montant)
            if montant <= 0:
                errors.append('Le montant doit être positif.')
            if montant > dette.montant_restant:
                errors.append(f'Le montant ne peut pas dépasser {dette.montant_restant:.0f} FCFA.')
        except ValueError:
            errors.append('Montant invalide.')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_obj = datetime.now().date()

        if errors:
            for error in errors:
                flash(error, 'danger')
            today = datetime.now().strftime('%Y-%m-%d')
            return render_template('debts/payment_add.html', dette=dette, today=today)

        # Création du paiement
        paiement = Paiement(
            montant=montant,
            date=date_obj,
            dette_id=dette.id
        )

        db.session.add(paiement)
        db.session.commit()

        # Envoyer confirmation au client si email confirmé
        client = dette.client
        if client.email and client.email_confirmed:
            from app.email_service import send_payment_confirmation_email
            send_payment_confirmation_email(client, paiement, dette)

        # Message de succès
        if dette.montant_restant <= 0:
            flash(f'Paiement de {montant:.0f} FCFA enregistré. Dette soldée !', 'success')
        else:
            flash(f'Paiement de {montant:.0f} FCFA enregistré. Reste: {dette.montant_restant:.0f} FCFA', 'success')

        return redirect(url_for('debts.dette_detail', id=dette_id))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('debts/payment_add.html', dette=dette, today=today)


@debts_bp.route('/paiement/<int:id>/delete', methods=['POST'])
@login_required
def delete_paiement(id):
    """Supprimer un paiement"""
    paiement = Paiement.query.join(Dette).join(Client).filter(
        Paiement.id == id,
        Client.user_id == current_user.id
    ).first_or_404()

    dette_id = paiement.dette_id
    db.session.delete(paiement)
    db.session.commit()

    flash('Paiement supprimé.', 'info')
    return redirect(url_for('debts.dette_detail', id=dette_id))

"""
Routes CRUD pour les transactions
Inclut: pagination, recherche, filtrage, export
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Transaction

# Création du Blueprint
transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

# Catégories prédéfinies
CATEGORIES = [
    'Vente',
    'Service',
    'Achat marchandise',
    'Salaire',
    'Loyer',
    'Électricité',
    'Eau',
    'Transport',
    'Téléphone',
    'Fournitures',
    'Autre'
]

# Nombre de transactions par page
PER_PAGE = 10


@transactions_bp.route('/')
@login_required
def list_transactions():
    """Liste de toutes les transactions avec filtrage, recherche et pagination"""
    # Paramètres de filtrage
    page = request.args.get('page', 1, type=int)
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')
    type_filter = request.args.get('type', '')
    category_filter = request.args.get('category', '')
    search = request.args.get('search', '').strip()

    # Query de base
    query = Transaction.query.filter_by(user_id=current_user.id)

    # Appliquer les filtres
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= date_debut_obj)
        except ValueError:
            pass

    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= date_fin_obj)
        except ValueError:
            pass

    if type_filter in ['recette', 'depense']:
        query = query.filter(Transaction.type == type_filter)

    if category_filter:
        query = query.filter(Transaction.category == category_filter)

    # Recherche dans la description
    if search:
        query = query.filter(Transaction.description.ilike(f'%{search}%'))

    # Trier par date décroissante avec pagination
    pagination = query.order_by(
        Transaction.date.desc(),
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=PER_PAGE, error_out=False)

    transactions = pagination.items

    # Calculer les totaux filtrés
    total_recettes_filtered = query.filter(Transaction.type == 'recette').with_entities(
        func.sum(Transaction.amount)).scalar() or 0
    total_depenses_filtered = query.filter(Transaction.type == 'depense').with_entities(
        func.sum(Transaction.amount)).scalar() or 0

    # Récupérer toutes les catégories utilisées par cet utilisateur (incluant les personnalisées)
    user_categories = db.session.query(Transaction.category).filter_by(
        user_id=current_user.id
    ).distinct().all()
    user_categories = [c[0] for c in user_categories if c[0]]

    # Fusionner avec les catégories prédéfinies (sans doublons)
    all_categories = list(CATEGORIES)
    for cat in user_categories:
        if cat not in all_categories:
            all_categories.append(cat)

    return render_template('transactions/list.html',
                           transactions=transactions,
                           pagination=pagination,
                           date_debut=date_debut,
                           date_fin=date_fin,
                           type_filter=type_filter,
                           category_filter=category_filter,
                           search=search,
                           categories=all_categories,
                           total_recettes=total_recettes_filtered,
                           total_depenses=total_depenses_filtered)


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """Ajouter une nouvelle transaction"""
    if request.method == 'POST':
        type_transaction = request.form.get('type', '')
        amount = request.form.get('amount', '')
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Autre')
        custom_category = request.form.get('custom_category', '').strip()
        date_str = request.form.get('date', '')

        # Si catégorie "Autre" et une catégorie personnalisée est fournie
        if category == 'Autre' and custom_category:
            category = custom_category

        # Validations
        errors = []

        if type_transaction not in ['recette', 'depense']:
            errors.append('Type de transaction invalide.')

        try:
            amount = float(amount)
            if amount <= 0:
                errors.append('Le montant doit être positif.')
        except ValueError:
            errors.append('Montant invalide.')

        if not description:
            errors.append('La description est obligatoire.')

        if len(description) > 200:
            errors.append('La description ne doit pas dépasser 200 caractères.')

        # Valider la catégorie personnalisée
        if category == 'Autre' and not custom_category:
            errors.append('Veuillez saisir une catégorie personnalisée.')

        if custom_category and len(custom_category) > 50:
            errors.append('La catégorie ne doit pas dépasser 50 caractères.')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_obj = datetime.now().date()

        if errors:
            for error in errors:
                flash(error, 'danger')
            today = datetime.now().strftime('%Y-%m-%d')
            return render_template('transactions/add.html', categories=CATEGORIES, today=today)

        # Création de la transaction
        transaction = Transaction(
            type=type_transaction,
            amount=amount,
            description=description,
            category=category,
            date=date_obj,
            user_id=current_user.id
        )

        db.session.add(transaction)
        db.session.commit()

        flash('Transaction ajoutée avec succès !', 'success')
        return redirect(url_for('transactions.list_transactions'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('transactions/add.html', categories=CATEGORIES, today=today)


@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    """Modifier une transaction existante"""
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        type_transaction = request.form.get('type', '')
        amount = request.form.get('amount', '')
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Autre')
        custom_category = request.form.get('custom_category', '').strip()
        date_str = request.form.get('date', '')

        # Si catégorie "Autre" et une catégorie personnalisée est fournie
        if category == 'Autre' and custom_category:
            category = custom_category

        # Validations
        errors = []

        if type_transaction not in ['recette', 'depense']:
            errors.append('Type de transaction invalide.')

        try:
            amount = float(amount)
            if amount <= 0:
                errors.append('Le montant doit être positif.')
        except ValueError:
            errors.append('Montant invalide.')

        if not description:
            errors.append('La description est obligatoire.')

        # Valider la catégorie personnalisée
        if category == 'Autre' and not custom_category:
            errors.append('Veuillez saisir une catégorie personnalisée.')

        if custom_category and len(custom_category) > 50:
            errors.append('La catégorie ne doit pas dépasser 50 caractères.')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_obj = transaction.date

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('transactions/edit.html',
                                   transaction=transaction,
                                   categories=CATEGORIES)

        # Mise à jour
        transaction.type = type_transaction
        transaction.amount = amount
        transaction.description = description
        transaction.category = category
        transaction.date = date_obj

        db.session.commit()

        flash('Transaction modifiée avec succès !', 'success')
        return redirect(url_for('transactions.list_transactions'))

    return render_template('transactions/edit.html',
                           transaction=transaction,
                           categories=CATEGORIES)


@transactions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    """Supprimer une transaction"""
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(transaction)
    db.session.commit()

    flash('Transaction supprimée.', 'info')
    return redirect(url_for('transactions.list_transactions'))


@transactions_bp.route('/export/csv')
@login_required
def export_csv():
    """Exporter les transactions en CSV"""
    # Récupérer toutes les transactions de l'utilisateur
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    # Générer le CSV
    csv_content = "Date,Type,Description,Catégorie,Montant\n"
    for t in transactions:
        csv_content += f"{t.date.strftime('%Y-%m-%d')},{t.type},{t.description},{t.category},{t.amount}\n"

    # Retourner comme fichier téléchargeable
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=transactions_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

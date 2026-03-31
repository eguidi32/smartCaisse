"""
Routes pour la gestion du stock (inventaire)
- Produits : liste, ajout, édition, suppression
- Mouvements : entrées, sorties, historique
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Product, StockMovement

# Création du Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ============================================
# DASHBOARD INVENTAIRE
# ============================================

@inventory_bp.route('/')
@login_required
def dashboard():
    """Dashboard inventaire - vue d'ensemble du stock"""
    products = Product.query.filter_by(user_id=current_user.id).all()

    # Statut du stock
    total_products = len(products)
    low_stock_products = [p for p in products if p.current_stock <= 5]
    total_stock = sum(p.current_stock for p in products)

    # Derniers mouvements
    recent_movements = db.session.query(StockMovement).join(Product).filter(
        Product.user_id == current_user.id
    ).order_by(StockMovement.created_at.desc()).limit(5).all()

    return render_template('inventory/dashboard.html',
                          total_products=total_products,
                          low_stock_products=low_stock_products,
                          total_stock=total_stock,
                          recent_movements=recent_movements,
                          products=products)


# ============================================
# GESTION DES PRODUITS
# ============================================

@inventory_bp.route('/products')
@login_required
def list_products():
    """Affiche la liste de tous les produits"""
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('inventory/products.html', products=products)


@inventory_bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Ajoute un nouveau produit"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', 0)

        # Validation
        if not name:
            flash('Le nom du produit est requis', 'danger')
            return redirect(url_for('inventory.add_product'))

        # Vérifier unicité du nom par utilisateur
        existing = Product.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            flash('Ce produit existe déjà', 'danger')
            return redirect(url_for('inventory.add_product'))

        try:
            product = Product(
                name=name,
                description=description,
                price=float(price) if price else 0.0,
                user_id=current_user.id
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Produit "{name}" créé avec succès', 'success')
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'danger')
            return redirect(url_for('inventory.add_product'))

    return render_template('inventory/product_add.html')


@inventory_bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """Édite un produit existant"""
    product = Product.query.get_or_404(id)

    # Vérifier que l'utilisateur est propriétaire du produit
    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', 0)

        if not name:
            flash('Le nom du produit est requis', 'danger')
            return redirect(url_for('inventory.edit_product', id=id))

        # Vérifier unicité du nom (sauf le produit actuel)
        existing = Product.query.filter_by(name=name, user_id=current_user.id).first()
        if existing and existing.id != product.id:
            flash('Ce nom de produit est déjà utilisé', 'danger')
            return redirect(url_for('inventory.edit_product', id=id))

        try:
            product.name = name
            product.description = description
            product.price = float(price) if price else 0.0
            db.session.commit()
            flash(f'Produit "{name}" mis à jour', 'success')
            return redirect(url_for('inventory.product_detail', id=product.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')

    return render_template('inventory/product_edit.html', product=product)


@inventory_bp.route('/product/<int:id>')
@login_required
def product_detail(id):
    """Affiche le détail d'un produit avec historique"""
    product = Product.query.get_or_404(id)

    # Vérifier que l'utilisateur est propriétaire
    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    movements = StockMovement.query.filter_by(product_id=id).order_by(
        StockMovement.created_at.desc()
    ).all()

    return render_template('inventory/product_detail.html',
                          product=product,
                          movements=movements)


@inventory_bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    """Supprime un produit"""
    product = Product.query.get_or_404(id)

    # Vérifier que l'utilisateur est propriétaire
    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    try:
        name = product.name
        db.session.delete(product)
        db.session.commit()
        flash(f'Produit "{name}" supprimé', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')

    return redirect(url_for('inventory.list_products'))


# ============================================
# GESTION DES MOUVEMENTS DE STOCK
# ============================================

@inventory_bp.route('/stock/add', methods=['GET', 'POST'])
@login_required
def add_stock_movement():
    """Ajoute un mouvement de stock (entrée ou sortie)"""
    products = Product.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        movement_type = request.form.get('type')  # 'entrée' ou 'sortie'
        quantity = request.form.get('quantity', type=int)
        notes = request.form.get('notes', '').strip()
        date = request.form.get('date') or datetime.utcnow().date()

        # Validation
        if not product_id or not movement_type or not quantity or quantity <= 0:
            flash('Tous les champs sont requis et la quantité doit être positive', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        # Vérifier que le produit existe et appartient à l'user
        product = Product.query.get_or_404(product_id)
        if product.user_id != current_user.id:
            flash('Accès refusé', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        # Vérifier que la sortie ne dépasse pas le stock
        if movement_type == 'sortie' and quantity > product.current_stock:
            flash(f'Stock insuffisant! Stock actuel: {product.current_stock}', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        try:
            movement = StockMovement(
                type=movement_type,
                quantity=quantity,
                notes=notes,
                date=date if isinstance(date, datetime) else datetime.strptime(date, '%Y-%m-%d').date(),
                product_id=product_id
            )
            db.session.add(movement)
            db.session.commit()

            action = "ajoutée au stock" if movement_type == 'entrée' else "retirée du stock"
            flash(f'{quantity} unité(s) {action}', 'success')
            return redirect(url_for('inventory.product_detail', id=product_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement: {str(e)}', 'danger')

    return render_template('inventory/stock_movement_add.html', products=products)


@inventory_bp.route('/stock/history')
@login_required
def stock_history():
    """Affiche l'historique complet des mouvements de stock"""
    # Filtrer par type si spécifié
    movement_type = request.args.get('type')  # 'entrée', 'sortie', ou None

    query = db.session.query(StockMovement).join(Product).filter(
        Product.user_id == current_user.id
    )

    if movement_type in ['entrée', 'sortie']:
        query = query.filter(StockMovement.type == movement_type)

    movements = query.order_by(StockMovement.created_at.desc()).all()

    return render_template('inventory/stock_history.html',
                          movements=movements,
                          current_type=movement_type)

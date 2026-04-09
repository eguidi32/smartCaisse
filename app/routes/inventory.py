"""
Routes pour la gestion du stock (inventaire) - VERSION 2.0
- Produits avec catégories et SKU
- Mouvements avec traçabilité
- Audit complet des modifications
- Pagination et recherche avancée
- Cache du stock pour performance
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
from app import db
from app.models import Product, StockMovement, ProductCategory, ProductHistory
from app.utils import log_audit

# Constante pagination (cohérent avec PER_PAGE du projet)
PER_PAGE = 10

# Création du Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ============================================
# HELPERS
# ============================================

def update_product_stock_cache(product_id):
    """Mettre à jour le cache du stock pour un produit"""
    product = Product.query.get(product_id)
    if not product:
        return

    entries = db.session.query(func.sum(StockMovement.quantity)).filter_by(
        product_id=product_id, type='entrée'
    ).scalar() or 0
    exits = db.session.query(func.sum(StockMovement.quantity)).filter_by(
        product_id=product_id, type='sortie'
    ).scalar() or 0

    product.stock_cache = entries - exits
    product.stock_cache_updated_at = datetime.utcnow()
    db.session.commit()


def track_product_change(product_id, field, old_value, new_value):
    """Enregistrer un changement de produit dans l'historique"""
    if old_value != new_value:
        history = ProductHistory(
            product_id=product_id,
            action='edited',
            field_changed=field,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            changed_by_id=current_user.id
        )
        db.session.add(history)


# ============================================
# DASHBOARD INVENTAIRE
# ============================================

@inventory_bp.route('/')
@login_required
def dashboard():
    """Dashboard inventaire avec pagination"""
    page = request.args.get('page', 1, type=int)

    # Stats globales (queries rapides)
    total_products = db.session.query(func.count(Product.id)).filter_by(
        user_id=current_user.id
    ).scalar()

    total_stock = db.session.query(func.sum(Product.stock_cache)).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    low_stock_count = db.session.query(func.count(Product.id)).filter(
        Product.user_id == current_user.id,
        Product.stock_cache <= 5
    ).scalar()

    # Produits paginés
    pagination = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name)\
        .paginate(page=page, per_page=PER_PAGE, error_out=False)

    products = pagination.items

    # Produits en stock faible (tous pour alerte)
    low_stock_products = Product.query.filter_by(user_id=current_user.id)\
        .filter(Product.stock_cache <= 5)\
        .order_by(Product.stock_cache)\
        .limit(5)\
        .all()

    # Derniers mouvements
    recent_movements = db.session.query(StockMovement)\
        .join(Product)\
        .filter(Product.user_id == current_user.id)\
        .order_by(StockMovement.created_at.desc())\
        .limit(5)\
        .all()

    return render_template('inventory/dashboard.html',
                          pagination=pagination,
                          products=products,
                          total_products=total_products,
                          total_stock=total_stock,
                          low_stock_count=low_stock_count,
                          low_stock_products=low_stock_products,
                          recent_movements=recent_movements)


# ============================================
# GESTION DES CATÉGORIES
# ============================================

def get_categories():
    """Récupère toutes les catégories de l'utilisateur"""
    return ProductCategory.query.filter_by(user_id=current_user.id)\
        .order_by(ProductCategory.name)\
        .all()


# ============================================
# GESTION DES CATÉGORIES
# ============================================

@inventory_bp.route('/categories')
@login_required
def list_categories():
    """Liste des catégories"""
    categories = get_categories()
    return render_template('inventory/categories.html', categories=categories)


@inventory_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Ajouter une nouvelle catégorie"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Le nom de la catégorie est requis', 'danger')
            return redirect(url_for('inventory.add_category'))

        # Vérifier unicité du nom par user
        existing = ProductCategory.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            flash('Cette catégorie existe déjà', 'danger')
            return redirect(url_for('inventory.add_category'))

        try:
            category = ProductCategory(
                name=name,
                description=description,
                user_id=current_user.id
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Catégorie "{name}" créée', 'success')
            return redirect(url_for('inventory.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('inventory/category_add.html')


@inventory_bp.route('/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Éditer une catégorie"""
    category = ProductCategory.query.get_or_404(id)

    if category.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Le nom est requis', 'danger')
            return redirect(url_for('inventory.edit_category', id=id))

        # Vérifier unicité (sauf self)
        existing = ProductCategory.query.filter_by(name=name, user_id=current_user.id).first()
        if existing and existing.id != category.id:
            flash('Ce nom existe déjà', 'danger')
            return redirect(url_for('inventory.edit_category', id=id))

        try:
            category.name = name
            category.description = description
            db.session.commit()
            flash(f'Catégorie "{name}" mise à jour', 'success')
            return redirect(url_for('inventory.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('inventory/category_edit.html', category=category)


@inventory_bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """Supprimer une catégorie"""
    category = ProductCategory.query.get_or_404(id)

    if category.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_categories'))

    # Vérifier que la catégorie n'a pas de produits
    products_count = Product.query.filter_by(category_id=id).count()
    if products_count > 0:
        flash(f'Impossible de supprimer: {products_count} produit(s) utilisent cette catégorie', 'danger')
        return redirect(url_for('inventory.list_categories'))

    try:
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f'Catégorie "{name}" supprimée', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')

    return redirect(url_for('inventory.list_categories'))


@inventory_bp.route('/products')
@login_required
def list_products():
    """Liste des produits avec recherche et filtrage"""
    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('q', '').strip()
    category_id = request.args.get('category', None, type=int)

    # Query de base
    query = Product.query.filter_by(user_id=current_user.id)

    # Filtre recherche (nom ou SKU)
    if search_q:
        query = query.filter(or_(
            Product.name.ilike(f'%{search_q}%'),
            Product.sku.ilike(f'%{search_q}%')
        ))

    # Filtre catégorie
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Pagination
    pagination = query.order_by(Product.name)\
        .paginate(page=page, per_page=PER_PAGE, error_out=False)

    categories = get_categories()

    return render_template('inventory/products.html',
                          pagination=pagination,
                          products=pagination.items,
                          categories=categories,
                          search_q=search_q,
                          current_category=category_id)


@inventory_bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip() or None
        description = request.form.get('description', '').strip()
        price = request.form.get('price', 0)
        category_id = request.form.get('category_id', None, type=int)

        # Validation
        if not name:
            flash('Le nom du produit est requis', 'danger')
            return redirect(url_for('inventory.add_product'))

        # Vérifier unicité du nom par user
        existing_name = Product.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_name:
            flash('Ce produit existe déjà', 'danger')
            return redirect(url_for('inventory.add_product'))

        # Vérifier unicité du SKU par user
        if sku:
            existing_sku = Product.query.filter_by(sku=sku, user_id=current_user.id).first()
            if existing_sku:
                flash('Ce SKU existe déjà', 'danger')
                return redirect(url_for('inventory.add_product'))

        try:
            product = Product(
                name=name,
                sku=sku,
                description=description,
                price=float(price) if price else 0.0,
                category_id=category_id if category_id else None,
                user_id=current_user.id
            )
            db.session.add(product)
            db.session.flush()

            # Créer historique
            history = ProductHistory(
                product_id=product.id,
                action='created',
                field_changed='création',
                old_value=None,
                new_value=f"{name} (SKU: {sku})" if sku else name,
                changed_by_id=current_user.id
            )
            db.session.add(history)
            db.session.commit()

            # Logger l'action
            log_audit('create', 'Product', entity_id=product.id, new_value=f'name={name}, sku={sku}, price={product.price}')

            flash(f'Produit "{name}" créé avec succès', 'success')
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    categories = get_categories()
    return render_template('inventory/product_add.html', categories=categories)


@inventory_bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """Éditer un produit"""
    product = Product.query.get_or_404(id)

    # Vérifier propriété
    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip() or None
        description = request.form.get('description', '').strip()
        price = request.form.get('price', 0)
        category_id = request.form.get('category_id', None, type=int)

        if not name:
            flash('Le nom du produit est requis', 'danger')
            return redirect(url_for('inventory.edit_product', id=id))

        # Vérifier unicité du nom (sauf self)
        existing_name = Product.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_name and existing_name.id != product.id:
            flash('Ce nom de produit est déjà utilisé', 'danger')
            return redirect(url_for('inventory.edit_product', id=id))

        # Vérifier unicité du SKU (sauf self)
        if sku:
            existing_sku = Product.query.filter_by(sku=sku, user_id=current_user.id).first()
            if existing_sku and existing_sku.id != product.id:
                flash('Ce SKU est déjà utilisé', 'danger')
                return redirect(url_for('inventory.edit_product', id=id))

        try:
            # Tracer les changements
            track_product_change(product.id, 'name', product.name, name)
            track_product_change(product.id, 'sku', product.sku, sku)
            track_product_change(product.id, 'description', product.description, description)
            track_product_change(product.id, 'price', product.price, float(price) if price else 0.0)
            track_product_change(product.id, 'category_id', product.category_id, category_id)

            # Mettre à jour
            product.name = name
            product.sku = sku
            product.description = description
            product.price = float(price) if price else 0.0
            product.category_id = category_id if category_id else None
            db.session.commit()

            # Logger l'action
            log_audit('update', 'Product', entity_id=product.id, new_value=f'name={name}, sku={sku}, price={product.price}')

            flash(f'Produit "{name}" mis à jour', 'success')
            return redirect(url_for('inventory.product_detail', id=product.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    categories = get_categories()
    return render_template('inventory/product_edit.html', product=product, categories=categories)


@inventory_bp.route('/product/<int:id>')
@login_required
def product_detail(id):
    """Détail d'un produit"""
    product = Product.query.get_or_404(id)

    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    # Mettre à jour le cache si expiré
    if not product.stock_cache_updated_at or \
       datetime.utcnow() - product.stock_cache_updated_at > timedelta(minutes=5):
        update_product_stock_cache(product.id)
        db.session.refresh(product)

    # Mouvements du produit
    movements = StockMovement.query.filter_by(product_id=id)\
        .order_by(StockMovement.created_at.desc())\
        .all()

    return render_template('inventory/product_detail.html',
                          product=product,
                          movements=movements)


@inventory_bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    """Supprimer un produit"""
    product = Product.query.get_or_404(id)

    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    try:
        name = product.name
        db.session.delete(product)
        db.session.commit()

        # Logger l'action
        log_audit('delete', 'Product', entity_id=id, new_value=f'deleted_product_name={name}')

        flash(f'Produit "{name}" supprimé', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')

    return redirect(url_for('inventory.list_products'))


# ============================================
# HISTORIQUE DES MODIFICATIONS
# ============================================

@inventory_bp.route('/product/<int:id>/history')
@login_required
def product_history(id):
    """Afficher l'historique des modification d'un produit"""
    product = Product.query.get_or_404(id)

    if product.user_id != current_user.id:
        flash('Accès refusé', 'danger')
        return redirect(url_for('inventory.list_products'))

    history = ProductHistory.query.filter_by(product_id=id)\
        .order_by(ProductHistory.changed_at.desc())\
        .all()

    return render_template('inventory/product_history.html',
                          product=product,
                          history=history)


# ============================================
# GESTION DES MOUVEMENTS DE STOCK
# ============================================

@inventory_bp.route('/stock/add', methods=['GET', 'POST'])
@login_required
def add_stock_movement():
    """Ajouter un mouvement de stock"""
    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name)\
        .all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        movement_type = request.form.get('type')
        quantity = request.form.get('quantity', type=int)
        reason = request.form.get('reason', '').strip()
        date = request.form.get('date') or datetime.utcnow().date()

        # Validation
        if not product_id or not movement_type or not quantity or quantity <= 0:
            flash('Tous les champs requis et quantité doit être positive', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        # Vérifier produit appartient à user
        product = Product.query.get_or_404(product_id)
        if product.user_id != current_user.id:
            flash('Accès refusé', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        # Vérifier stock suffisant pour sortie
        if movement_type == 'sortie' and quantity > product.current_stock:
            flash(f'Stock insuffisant! Stock: {product.current_stock}', 'danger')
            return redirect(url_for('inventory.add_stock_movement'))

        try:
            movement = StockMovement(
                type=movement_type,
                quantity=quantity,
                reason=reason,
                date=date if isinstance(date, datetime) else datetime.strptime(date, '%Y-%m-%d').date(),
                product_id=product_id,
                created_by_id=current_user.id
            )
            db.session.add(movement)
            db.session.commit()

            # Logger l'action
            log_audit('create', 'StockMovement', entity_id=movement.id, new_value=f'type={movement_type}, quantity={quantity}, product_id={product_id}')

            # Mettre à jour cache
            update_product_stock_cache(product_id)

            action = "ajoutée" if movement_type == 'entrée' else "retirée"
            flash(f'{quantity} unité(s) {action} du stock', 'success')
            return redirect(url_for('inventory.product_detail', id=product_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('inventory/stock_movement_add.html', products=products)


@inventory_bp.route('/stock/history')
@login_required
def stock_history():
    """Historique complet des mouvements"""
    page = request.args.get('page', 1, type=int)
    movement_type = request.args.get('type')
    product_id = request.args.get('product_id', type=int)
    date_start = request.args.get('date_start')
    date_end = request.args.get('date_end')

    query = db.session.query(StockMovement)\
        .join(Product)\
        .filter(Product.user_id == current_user.id)

    # Filtres
    if movement_type in ['entrée', 'sortie']:
        query = query.filter(StockMovement.type == movement_type)

    if product_id:
        query = query.filter(StockMovement.product_id == product_id)

    if date_start:
        query = query.filter(StockMovement.date >= date_start)

    if date_end:
        query = query.filter(StockMovement.date <= date_end)

    # Pagination
    pagination = query.order_by(StockMovement.created_at.desc())\
        .paginate(page=page, per_page=PER_PAGE, error_out=False)

    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name)\
        .all()

    return render_template('inventory/stock_history.html',
                          pagination=pagination,
                          movements=pagination.items,
                          products=products,
                          current_type=movement_type,
                          current_product=product_id,
                          date_start=date_start,
                          date_end=date_end)


# ============================================
# EXPORTS PDF / EXCEL
# ============================================

@inventory_bp.route('/export/pdf')
@login_required
def export_pdf():
    """Exporter l'inventaire en PDF"""
    from flask import send_file
    from app.exports.pdf_generator import PDFGenerator

    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name).all()

    generator = PDFGenerator("Inventaire")
    pdf_buffer = generator.generate_inventory_pdf(products, current_user.username)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'inventaire_{datetime.now().strftime("%Y%m%d")}.pdf'
    )


@inventory_bp.route('/movements/export/pdf')
@login_required
def export_movements_pdf():
    """Exporter les mouvements de stock en PDF"""
    from flask import send_file
    from app.exports.pdf_generator import PDFGenerator

    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name).all()

    generator = PDFGenerator("Mouvements de Stock")
    pdf_buffer = generator.generate_movements_pdf(products, current_user.username)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'mouvements_stock_{datetime.now().strftime("%Y%m%d")}.pdf'
    )


@inventory_bp.route('/export/excel')
@login_required
def export_excel():
    """Exporter l'inventaire en Excel"""
    from flask import send_file
    from app.exports.excel_generator import ExcelGenerator
    
    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name).all()
    
    generator = ExcelGenerator("Inventaire")
    excel_buffer = generator.generate_inventory_excel(products, current_user.username)
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'inventaire_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

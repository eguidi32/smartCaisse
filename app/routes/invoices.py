from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Invoice, InvoiceItem, Client, Product, StockMovement
from app.exports.pdf_generator import PDFGenerator
from app.exports.excel_generator import ExcelGenerator
from app.utils import log_audit

bp = Blueprint('invoices', __name__, url_prefix='/invoices')


@bp.route('/')
@login_required
def index():
    """Liste des factures avec pagination"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Invoice.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Invoice.numero.ilike(f'%{search}%'),
                Invoice.client_name.ilike(f'%{search}%')
            )
        )
    
    query = query.order_by(Invoice.date.desc(), Invoice.id.desc())
    
    invoices = query.paginate(page=page, per_page=10, error_out=False)
    
    # Statistiques
    stats = {
        'total': Invoice.query.filter_by(user_id=current_user.id).count(),
        'brouillon': Invoice.query.filter_by(user_id=current_user.id, status='brouillon').count(),
        'payee': Invoice.query.filter_by(user_id=current_user.id, status='payée').count(),
        'montant_total': db.session.query(db.func.sum(Invoice.total)).filter_by(
            user_id=current_user.id, status='payée'
        ).scalar() or 0
    }
    
    return render_template('invoices/list.html',
                          invoices=invoices,
                          stats=stats,
                          status_filter=status_filter,
                          search=search)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Créer une nouvelle facture"""
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Déterminer le nom du client
        if client_id:
            client = Client.query.filter_by(id=client_id, user_id=current_user.id).first()
            if client:
                client_name = client.nom
        
        if not client_name:
            flash('Veuillez spécifier un client.', 'danger')
            return redirect(url_for('invoices.create'))
        
        # Créer la facture
        invoice = Invoice(
            numero=Invoice.generate_numero(current_user.id),
            client_id=client_id if client_id else None,
            client_name=client_name,
            notes=notes,
            user_id=current_user.id
        )
        db.session.add(invoice)
        db.session.flush()  # Pour obtenir l'ID
        
        # Ajouter les articles
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        for i, product_id in enumerate(product_ids):
            if product_id and product_id.strip():  # Vérifie que product_id n'est pas vide
                product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
                if product:
                    qty_str = quantities[i] if i < len(quantities) else '1'
                    try:
                        qty = int(qty_str) if qty_str and qty_str.strip() else 1
                        if qty <= 0:
                            qty = 1
                    except (ValueError, TypeError):
                        qty = 1

                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=qty,
                        unit_price=product.price
                    )
                    item.calculate_total()
                    db.session.add(item)
        
        # Calculer le total
        db.session.flush()
        invoice.calculate_total()
        db.session.commit()

        # Logger l'action
        log_audit('create', 'Invoice', entity_id=invoice.id, new_value=f'numero={invoice.numero}, client={client_name}, total={invoice.total}')

        current_app.logger.info(f'Facture créée: {invoice.numero} par {current_user.username}')
        flash(f'Facture {invoice.numero} créée avec succès!', 'success')
        return redirect(url_for('invoices.detail', id=invoice.id))
    
    # GET: Afficher le formulaire
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.nom).all()
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    
    return render_template('invoices/create.html', clients=clients, products=products)


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Détail d'une facture"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('invoices/detail.html', invoice=invoice)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Éditer une facture (si brouillon)"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if not invoice.is_editable:
        flash('Cette facture ne peut plus être modifiée.', 'warning')
        return redirect(url_for('invoices.detail', id=id))
    
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Déterminer le nom du client
        if client_id:
            client = Client.query.filter_by(id=client_id, user_id=current_user.id).first()
            if client:
                client_name = client.nom
        
        if not client_name:
            flash('Veuillez spécifier un client.', 'danger')
            return redirect(url_for('invoices.edit', id=id))
        
        # Mettre à jour la facture
        invoice.client_id = client_id if client_id else None
        invoice.client_name = client_name
        invoice.notes = notes
        
        # Supprimer les anciens articles
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
        
        # Ajouter les nouveaux articles
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        for i, product_id in enumerate(product_ids):
            if product_id and product_id.strip():  # Vérifie que product_id n'est pas vide
                product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
                if product:
                    qty_str = quantities[i] if i < len(quantities) else '1'
                    try:
                        qty = int(qty_str) if qty_str and qty_str.strip() else 1
                        if qty <= 0:
                            qty = 1
                    except (ValueError, TypeError):
                        qty = 1

                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=qty,
                        unit_price=product.price
                    )
                    item.calculate_total()
                    db.session.add(item)
        
        # Recalculer le total
        db.session.flush()
        invoice.calculate_total()
        db.session.commit()

        # Logger l'action
        log_audit('update', 'Invoice', entity_id=invoice.id, new_value=f'numero={invoice.numero}, client={client_name}, total={invoice.total}')

        current_app.logger.info(f'Facture modifiée: {invoice.numero} par {current_user.username}')
        flash('Facture mise à jour!', 'success')
        return redirect(url_for('invoices.detail', id=invoice.id))
    
    # GET: Afficher le formulaire
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.nom).all()
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    
    return render_template('invoices/edit.html', invoice=invoice, clients=clients, products=products)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer une facture et reverser les mouvements de stock si nécessaire"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    numero = invoice.numero
    product_ids_to_update = set()

    # Si la facture a été confirmée (envoyée), reverser les mouvements de stock
    if invoice.status == 'envoyée':
        for item in invoice.items:
            # Créer un mouvement de stock inverse (entrée) pour annuler la sortie
            reverse_movement = StockMovement(
                product_id=item.product_id,
                type='entrée',
                quantity=item.quantity,
                reason=f'Annulation facture {invoice.numero}',
                notes=f'Retour de stock suite suppression facture',
                created_by_id=current_user.id
            )
            db.session.add(reverse_movement)
            product_ids_to_update.add(item.product_id)

    db.session.delete(invoice)
    db.session.commit()

    # Mettre à jour le cache du stock pour chaque produit
    if product_ids_to_update:
        from app.routes.inventory import update_product_stock_cache
        for product_id in product_ids_to_update:
            update_product_stock_cache(product_id)

    # Logger l'action
    log_audit('delete', 'Invoice', entity_id=id, new_value=f'deleted_invoice_numero={numero}')

    current_app.logger.info(f'Facture supprimée: {numero} par {current_user.username}')
    flash(f'Facture {numero} supprimée.', 'success')
    return redirect(url_for('invoices.index'))


@bp.route('/<int:id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(id):
    """Marquer une facture comme payée"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Vérifier que la facture est envoyée avant de la marquer payée
    if invoice.status != 'envoyée':
        flash(f'Impossible - la facture doit être envoyée avant d\'être payée.', 'danger')
        return redirect(url_for('invoices.detail', id=id))

    invoice.mark_as_paid()
    db.session.commit()

    # Logger l'action
    log_audit('update', 'Invoice', entity_id=invoice.id, new_value=f'status_changed_to=payée, numero={invoice.numero}')

    current_app.logger.info(f'Facture payée: {invoice.numero} par {current_user.username}')
    flash(f'Facture {invoice.numero} marquée comme payée!', 'success')
    return redirect(url_for('invoices.detail', id=id))


@bp.route('/<int:id>/send', methods=['POST'])
@login_required
def send_invoice(id):
    """Marquer une facture comme envoyée, créer les mouvements de stock, et envoyer email"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if invoice.status == 'brouillon':
        # Vérifier que le stock est suffisant pour tous les articles
        stock_errors = []
        for item in invoice.items:
            product = Product.query.get(item.product_id)
            if not product:
                stock_errors.append(f'Produit {item.product_name} non trouvé')
                continue

            if product.stock_cache <= 0:
                stock_errors.append(f'{product.name}: stock vide (0 unitéS)')
            elif product.stock_cache < item.quantity:
                stock_errors.append(f'{product.name}: stock insuffisant ({product.stock_cache} disponibles, {item.quantity} demandées)')

        if stock_errors:
            flash('Impossible d\'envoyer la facture - Stock insuffisant:', 'danger')
            for error in stock_errors:
                flash(error, 'danger')
            return redirect(url_for('invoices.detail', id=id))

        invoice.status = 'envoyée'

        # Créer les mouvements de stock (sortie) pour chaque article
        product_ids_to_update = set()
        for item in invoice.items:
            stock_movement = StockMovement(
                product_id=item.product_id,
                type='sortie',
                quantity=item.quantity,
                reason=f'Facture {invoice.numero}',
                notes=f'Vendu via facture à {invoice.client_name}',
                created_by_id=current_user.id
            )
            db.session.add(stock_movement)
            product_ids_to_update.add(item.product_id)

        db.session.commit()

        # Mettre à jour le cache du stock pour chaque produit
        from app.routes.inventory import update_product_stock_cache
        for product_id in product_ids_to_update:
            update_product_stock_cache(product_id)

        # Envoyer l'email avec PDF
        from app.email_service import send_invoice_email
        client = None
        if invoice.client_id:
            client = Client.query.filter_by(id=invoice.client_id, user_id=current_user.id).first()

        if client and client.email:
            send_invoice_email(invoice, client, current_user)

        # Logger l'action
        log_audit('update', 'Invoice', entity_id=invoice.id, new_value=f'status_changed_to=envoyée, numero={invoice.numero}')

        current_app.logger.info(f'Facture confirmée et stock réduit: {invoice.numero} par {current_user.username}')
        flash(f'Facture {invoice.numero} confirmée! Stock réduit.', 'success')

    return redirect(url_for('invoices.detail', id=id))


@bp.route('/<int:id>/pdf')
@login_required
def download_pdf(id):
    """Télécharger la facture en PDF"""
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    generator = PDFGenerator(f"Facture {invoice.numero}")
    pdf_buffer = generator.generate_invoice_pdf(invoice, current_user)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'facture_{invoice.numero}.pdf'
    )


# ====================
# ROUTES D'EXPORT
# ====================

@bp.route('/export/pdf')
@login_required
def export_pdf():
    """Exporter la liste des factures en PDF"""
    invoices = Invoice.query.filter_by(user_id=current_user.id)\
        .order_by(Invoice.date.desc()).all()
    
    generator = PDFGenerator("Liste des factures")
    pdf_buffer = generator.generate_invoices_list_pdf(invoices, current_user.username)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'factures_{datetime.now().strftime("%Y%m%d")}.pdf'
    )


@bp.route('/export/excel')
@login_required
def export_excel():
    """Exporter la liste des factures en Excel"""
    invoices = Invoice.query.filter_by(user_id=current_user.id)\
        .order_by(Invoice.date.desc()).all()
    
    generator = ExcelGenerator("Liste des factures")
    excel_buffer = generator.generate_invoices_excel(invoices, current_user.username)
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'factures_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

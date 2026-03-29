"""
Routes pour les rapports et exports PDF
"""
from flask import Blueprint, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from app import db
from app.models import Transaction

# Création du Blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/pdf')
@login_required
def export_pdf():
    """Générer un rapport PDF des transactions"""
    # Récupérer les transactions
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    if not transactions:
        flash('Aucune transaction à exporter.', 'warning')
        return redirect(url_for('transactions.list_transactions'))

    # Calculer les totaux
    total_recettes = sum(t.amount for t in transactions if t.type == 'recette')
    total_depenses = sum(t.amount for t in transactions if t.type == 'depense')
    benefice = total_recettes - total_depenses

    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=30
    )
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10
    )

    # Titre
    elements.append(Paragraph("SmartCaisse - Rapport Financier", title_style))
    elements.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} pour {current_user.username}",
        subtitle_style
    ))

    # Résumé
    elements.append(Paragraph("Résumé", section_style))
    summary_data = [
        ['Total Recettes', f"{total_recettes:,.2f} FCFA"],
        ['Total Dépenses', f"{total_depenses:,.2f} FCFA"],
        ['Bénéfice Net', f"{benefice:,.2f} FCFA"],
        ['Nombre de transactions', str(len(transactions))]
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Liste des transactions
    elements.append(Paragraph("Détail des transactions", section_style))

    # En-tête du tableau
    table_data = [['Date', 'Type', 'Description', 'Catégorie', 'Montant']]

    # Données
    for t in transactions:
        type_label = 'Recette' if t.type == 'recette' else 'Dépense'
        amount_str = f"+{t.amount:,.2f}" if t.type == 'recette' else f"-{t.amount:,.2f}"
        table_data.append([
            t.date.strftime('%d/%m/%Y'),
            type_label,
            t.description[:30] + '...' if len(t.description) > 30 else t.description,
            t.category,
            amount_str
        ])

    # Créer le tableau
    transactions_table = Table(table_data, colWidths=[2.5*cm, 2*cm, 6*cm, 3*cm, 3*cm])
    transactions_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.8)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        # Alternance de couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(transactions_table)

    # Générer le PDF
    doc.build(elements)

    # Retourner le PDF
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename=rapport_smartcaisse_{datetime.now().strftime("%Y%m%d")}.pdf'
        }
    )


@reports_bp.route('/pdf/monthly/<int:year>/<int:month>')
@login_required
def export_pdf_monthly(year, month):
    """Générer un rapport PDF pour un mois spécifique"""
    from datetime import date
    from calendar import monthrange

    # Dates du mois
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    # Récupérer les transactions du mois
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).order_by(Transaction.date.desc()).all()

    if not transactions:
        flash(f'Aucune transaction pour {month:02d}/{year}.', 'warning')
        return redirect(url_for('main.stats'))

    # Calculer les totaux
    total_recettes = sum(t.amount for t in transactions if t.type == 'recette')
    total_depenses = sum(t.amount for t in transactions if t.type == 'depense')
    benefice = total_recettes - total_depenses

    # Créer le PDF (même logique que export_pdf mais avec titre différent)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                  fontSize=18, alignment=TA_CENTER, spaceAfter=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'],
                                     fontSize=10, alignment=TA_CENTER,
                                     textColor=colors.grey, spaceAfter=30)

    # Nom du mois en français
    mois_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    elements.append(Paragraph(f"Rapport - {mois_fr[month-1]} {year}", title_style))
    elements.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y')} pour {current_user.username}",
        subtitle_style
    ))

    # Résumé
    summary_data = [
        ['Total Recettes', f"{total_recettes:,.2f} FCFA"],
        ['Total Dépenses', f"{total_depenses:,.2f} FCFA"],
        ['Bénéfice Net', f"{benefice:,.2f} FCFA"],
        ['Transactions', str(len(transactions))]
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Transactions
    table_data = [['Date', 'Type', 'Description', 'Catégorie', 'Montant']]
    for t in transactions:
        type_label = 'Recette' if t.type == 'recette' else 'Dépense'
        amount_str = f"+{t.amount:,.2f}" if t.type == 'recette' else f"-{t.amount:,.2f}"
        table_data.append([
            t.date.strftime('%d/%m'),
            type_label,
            t.description[:30] + '...' if len(t.description) > 30 else t.description,
            t.category,
            amount_str
        ])

    transactions_table = Table(table_data, colWidths=[2*cm, 2*cm, 6.5*cm, 3*cm, 3*cm])
    transactions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.8)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(transactions_table)

    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename=rapport_{mois_fr[month-1]}_{year}.pdf'
        }
    )

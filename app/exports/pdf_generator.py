"""
Générateur de fichiers PDF pour SmartCaisse
Utilise reportlab pour créer des documents PDF
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class PDFGenerator:
    """Générateur de documents PDF pour SmartCaisse"""
    
    def __init__(self, title="Document SmartCaisse"):
        self.title = title
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7f8c8d')
        ))
        self.styles.add(ParagraphStyle(
            name='RightAligned',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
    
    def _create_header(self, elements, subtitle=None):
        """Crée l'en-tête du document"""
        elements.append(Paragraph(self.title, self.styles['CustomTitle']))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['CustomSubtitle']))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['CustomSubtitle']
        ))
        elements.append(Spacer(1, 20))
    
    def _create_table(self, data, col_widths=None):
        """Crée une table stylisée"""
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            # Alternance couleurs lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        return table
    
    def generate_inventory_pdf(self, products, user_name=""):
        """Génère un PDF de l'inventaire"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []

        self._create_header(elements, f"Inventaire de {user_name}" if user_name else "Inventaire complet")

        # Données du tableau
        data = [['Produit', 'SKU', 'Catégorie', 'Prix', 'Stock', 'Valeur']]
        total_value = 0

        for product in products:
            stock = product.current_stock
            value = stock * product.price
            total_value += value
            data.append([
                product.name,
                product.sku or '-',
                product.category.name if product.category else '-',
                f"{product.price:.0f} FCFA",
                str(stock),
                f"{value:.0f} FCFA"
            ])

        # Ligne total
        data.append(['', '', '', '', 'TOTAL:', f"{total_value:.0f} FCFA"])

        table = self._create_table(data, col_widths=[5*cm, 2.5*cm, 3*cm, 2.5*cm, 1.5*cm, 3*cm])
        elements.append(table)

        # Résumé
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"<b>Nombre de produits:</b> {len(products)} | <b>Valeur totale du stock:</b> {total_value:.0f} FCFA",
            self.styles['Normal']
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_movements_pdf(self, products, user_name=""):
        """Génère un PDF avec liste complète des mouvements de stock"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=0.8*cm, leftMargin=0.8*cm,
                               topMargin=2*cm, bottomMargin=2.5*cm)
        elements = []

        # En-tête
        self._create_header(elements, f"Mouvements de Stock - {user_name}" if user_name else "Mouvements de Stock")

        # Collecter tous les mouvements
        all_movements = []
        for product in products:
            movements = product.movements.all()
            for move in movements:
                all_movements.append({
                    'product_name': product.name,
                    'sku': product.sku or '-',
                    'price': product.price,
                    'date': move.date,
                    'type': move.type,
                    'quantity': move.quantity,
                    'notes': move.notes or ''
                })

        # Vérifier s'il y a des mouvements
        if not all_movements:
            elements.append(Paragraph("Aucun mouvement de stock enregistré.", self.styles['Normal']))
            doc.build(elements)
            buffer.seek(0)
            return buffer

        # Trier par date décroissante
        all_movements.sort(key=lambda x: x['date'], reverse=True)

        # Tableau complet des mouvements
        data = [['Date', 'Produit', 'Code', 'Type', 'Quantité', 'Prix Unit.', 'Valeur']]

        for move in all_movements:
            type_label = "Entrée" if move['type'] == 'entrée' else "Sortie"
            valeur = move['quantity'] * move['price']

            data.append([
                move['date'].strftime("%d/%m/%Y"),
                move['product_name'],
                move['sku'],
                type_label,
                f"{move['quantity']}",
                f"{move['price']:.0f}",
                f"{valeur:.0f}"
            ])

        table = self._create_movements_table(data)
        elements.append(table)

        # Notes additionelles si existent
        has_notes = any(move['notes'] for move in all_movements)
        if has_notes:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("<b>Observations:</b>", self.styles['Normal']))
            for move in all_movements:
                if move['notes']:
                    elements.append(Paragraph(
                        f"• {move['date'].strftime('%d/%m/%Y')} - {move['product_name']}: {move['notes']}",
                        self.styles['Normal']
                    ))

        # Footer
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"<i>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par SmartCaisse</i>",
            self.styles['RightAligned']
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _create_movements_table(self, data):
        """Crée le tableau des mouvements avec coloration - optimisé pour lisibilité"""
        # Colonnes élargies pour utiliser toute la largeur disponible
        table = Table(data, colWidths=[2*cm, 4*cm, 2*cm, 2*cm, 2*cm, 2.2*cm, 2.2*cm])

        # Créer le style du tableau
        style_list = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            # Corps
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Type centré
            ('ALIGN', (4, 1), (6, -1), 'RIGHT'),   # Chiffres à droite
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            # Alternance couleurs
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]

        # Colorer les lignes selon le type de mouvement
        for i in range(1, len(data)):
            if data[i][3] == 'Entrée':  # Type colonne 3
                style_list.append(('BACKGROUND', (3, i), (3, i), colors.HexColor('#d5f4e6')))
                style_list.append(('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#27ae60')))
                style_list.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))
            else:  # Sortie
                style_list.append(('BACKGROUND', (3, i), (3, i), colors.HexColor('#fadbd8')))
                style_list.append(('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#c0392b')))
                style_list.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))

        table.setStyle(TableStyle(style_list))
        return table

    def _create_summary_table_2cols(self, data):
        """Crée une table de résumé en 2 colonnes"""
        table = Table(data, colWidths=[6*cm, 2*cm])
        table.setStyle(TableStyle([
            # En-tête style
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            # Grille
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#95a5a6')),
        ]))
        return table

    def generate_debts_pdf(self, clients, user_name=""):
        """Génère un PDF des dettes clients"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        self._create_header(elements, f"Dettes clients de {user_name}" if user_name else "Liste des dettes")
        
        # Données du tableau
        data = [['Client', 'Téléphone', 'Total dettes', 'Total payé', 'Reste à payer']]
        total_dettes = 0
        total_paye = 0
        total_restant = 0
        
        for client in clients:
            total_dettes += client.total_dette
            total_paye += client.total_paye
            total_restant += client.total_restant
            data.append([
                client.nom,
                client.telephone,
                f"{client.total_dette:.0f} FCFA",
                f"{client.total_paye:.0f} FCFA",
                f"{client.total_restant:.0f} FCFA"
            ])
        
        # Ligne total
        data.append(['TOTAL', '', f"{total_dettes:.0f} FCFA", f"{total_paye:.0f} FCFA", f"{total_restant:.0f} FCFA"])
        
        table = self._create_table(data, col_widths=[4*cm, 3*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        elements.append(table)
        
        # Résumé
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"<b>Nombre de clients:</b> {len(clients)} | <b>Total à récupérer:</b> {total_restant:.0f} FCFA",
            self.styles['Normal']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_transactions_pdf(self, transactions, user_name="", period=""):
        """Génère un PDF des transactions"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        subtitle = f"Transactions de {user_name}" if user_name else "Transactions"
        if period:
            subtitle += f" - {period}"
        self._create_header(elements, subtitle)
        
        # Données du tableau
        data = [['Date', 'Type', 'Description', 'Catégorie', 'Montant']]
        total_recettes = 0
        total_depenses = 0
        
        for t in transactions:
            if t.type == 'recette':
                total_recettes += t.amount
                montant = f"+{t.amount:.0f} FCFA"
            else:
                total_depenses += t.amount
                montant = f"-{t.amount:.0f} FCFA"
            
            data.append([
                t.date.strftime('%d/%m/%Y'),
                'Recette' if t.type == 'recette' else 'Dépense',
                t.description[:30] + '...' if len(t.description) > 30 else t.description,
                t.category or '-',
                montant
            ])
        
        table = self._create_table(data, col_widths=[2.5*cm, 2*cm, 6*cm, 3*cm, 3*cm])
        elements.append(table)
        
        # Résumé
        solde = total_recettes - total_depenses
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"<b>Recettes:</b> +{total_recettes:.0f} FCFA | <b>Dépenses:</b> -{total_depenses:.0f} FCFA | <b>Solde:</b> {solde:.0f} FCFA",
            self.styles['Normal']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_invoice_pdf(self, invoice, user=None):
        """Génère un PDF de facture professionnel"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []

        # Nom de la boutique (company_name ou username)
        shop_name = (user.company_name if user and user.company_name else
                     (user.username if user else 'SmartCaisse'))

        # En-tête: FACTURE au-dessus et centré
        title_data = [[Paragraph(f"<font size=18><b>FACTURE</b></font>", self.styles['Normal'])]]
        title_table = Table(title_data, colWidths=[16*cm])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(title_table)

        # Infos boutique et numéro
        header_data = [
            [
                Paragraph(f"<font size=12><b>{shop_name}</b></font>", self.styles['Normal']),
                Paragraph(f"<b>{invoice.numero}</b>", self.styles['RightAligned'])
            ]
        ]
        header_table = Table(header_data, colWidths=[12*cm, 4*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(header_table)

        # Infos entreprise supplémentaires (si disponible)
        if user and user.company_name:
            elements.append(Spacer(1, 10))
            company_info = f"<b>{user.company_name}</b>"
            if user.company_address:
                company_info += f"<br/>{user.company_address}"
            if user.company_phone or user.company_email:
                company_info += "<br/>"
                if user.company_phone:
                    company_info += f"Tél: {user.company_phone}"
                if user.company_email:
                    company_info += f" | Email: {user.company_email}"
            if user.company_registration or user.company_tax_id:
                company_info += "<br/><font size=8>"
                if user.company_registration:
                    company_info += f"RCCM: {user.company_registration} "
                if user.company_tax_id:
                    company_info += f"IFU: {user.company_tax_id}"
                company_info += "</font>"
            
            elements.append(Paragraph(company_info, self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Infos facture et client
        invoice_data = [
            ['Date:', invoice.date.strftime('%d/%m/%Y'), 'Client:', invoice.client_name],
            ['Statut:', invoice.status.capitalize(), '', '']
        ]
        invoice_table = Table(invoice_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 20))
        
        # Tableau des articles
        data = [['Produit', 'Quantité', 'Prix unitaire', 'Total']]
        for item in invoice.items:
            data.append([
                item.product_name,
                str(item.quantity),
                f"{item.unit_price:.0f} FCFA",
                f"{item.total:.0f} FCFA"
            ])
        
        # Total
        data.append(['', '', 'TOTAL:', f"{invoice.total:.0f} FCFA"])
        
        table = self._create_table(data, col_widths=[7*cm, 2.5*cm, 3.5*cm, 3.5*cm])
        elements.append(table)
        
        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(f"<b>Notes:</b> {invoice.notes}", self.styles['Normal']))
        
        # Pied de page professionnel
        elements.append(Spacer(1, 40))
        footer_text = f"Facture générée par SmartCaisse le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        if user and user.company_website:
            footer_text += f" | {user.company_website}"
        elements.append(Paragraph(footer_text, self.styles['CustomSubtitle']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_invoices_list_pdf(self, invoices, user_name=""):
        """Génère un PDF de la liste des factures"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        self._create_header(elements, f"Factures de {user_name}" if user_name else "Liste des factures")
        
        # Données du tableau
        data = [['Numéro', 'Date', 'Client', 'Total', 'Statut']]
        total_montant = 0
        
        for inv in invoices:
            total_montant += inv.total
            data.append([
                inv.numero,
                inv.date.strftime('%d/%m/%Y'),
                inv.client_name,
                f"{inv.total:.0f} FCFA",
                inv.status.capitalize()
            ])
        
        # Ligne total
        data.append(['', '', 'TOTAL:', f"{total_montant:.0f} FCFA", ''])
        
        table = self._create_table(data, col_widths=[4*cm, 3*cm, 4*cm, 3.5*cm, 3*cm])
        elements.append(table)
        
        # Résumé
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"<b>Nombre de factures:</b> {len(invoices)} | <b>Montant total:</b> {total_montant:.0f} FCFA",
            self.styles['Normal']
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_audit_logs_pdf(self, logs, config):
        """Génère un PDF de rapport d'audit logs"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=0.8*cm, leftMargin=0.8*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
        elements = []

        self._create_header(elements, "Rapport Audit Logs")
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['CustomSubtitle']
        ))
        elements.append(Spacer(1, 15))

        # Tableau des audit logs
        data = [['Timestamp', 'Utilisateur', 'Action', 'Entité', 'IP', 'Statut', 'Détails']]

        for log in logs[:100]:  # Limiter à 100 logs par PDF
            username = log.user.username if log.user else "System"
            timestamp = log.timestamp.strftime('%d/%m %H:%M')
            details = ""
            if log.reason:
                details = log.reason[:30]
            elif log.new_value:
                details = log.new_value[:30]

            status_text = "✓ OK" if log.status == 'success' else "✗ ERR"

            data.append([
                timestamp,
                username,
                log.action,
                log.entity_type,
                log.ip_address or '-',
                status_text,
                details
            ])

        table = self._create_table(data, col_widths=[2*cm, 2*cm, 2*cm, 1.8*cm, 1.5*cm, 1.2*cm, 3.5*cm])

        # Appliquer les styles
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))

        elements.append(table)

        # Résumé
        elements.append(Spacer(1, 15))
        summary_text = f"<b>Total logs affichés:</b> {min(len(logs), 100)}"
        if len(logs) > 100:
            summary_text += f" (sur {len(logs)} au total)"
        elements.append(Paragraph(summary_text, self.styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        return buffer

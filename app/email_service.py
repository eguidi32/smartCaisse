"""
Service d'envoi d'emails pour SmartCaisse
Centralise la logique d'email pour notifications de dettes
"""
from flask import current_app, url_for
from flask_mail import Message
from app import mail


def send_client_registration_email(client):
    """
    Envoie un email de bienvenue au client avec lien de confirmation

    Args:
        client: Objet Client créé (avec token déjà sauvegardé)
    """
    # Récupérer le token déjà sauvegardé en BDD
    token = client.email_confirmation_token

    # Build confirmation URL using BASE_URL for production compatibility
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    confirmation_url = f"{base_url}/debts/email-confirmation/{token}"

    # Mode développement: affichage console
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 70)
        print('MODE DEVELOPPEMENT - Email de bienvenue client:')
        print(f'Destinataire: {client.email}')
        print(f'Client: {client.nom}')
        print(f'Dettes actuelles: {client.total_dette:.2f} FCFA')
        print(f'Token: {token}')
        print(f'Lien de confirmation: {confirmation_url}')
        print('=' * 70 + '\n')
        return True

    # Construire le message
    msg = Message(
        subject='SmartCaisse - Bienvenue ! Confirmez votre email',
        recipients=[client.email]
    )

    # Affichage des dettes actuelles du client
    dettes_html = ''
    if client.total_dette > 0:
        dettes_html = f'''
        <div style="margin-top: 20px; background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="color: #333; margin-top: 0;">Récapitulatif de vos dettes:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #e9ecef; border-bottom: 2px solid #dee2e6;">
                    <th style="padding: 10px; text-align: left;">Description</th>
                    <th style="padding: 10px; text-align: right;">Montant</th>
                    <th style="padding: 10px; text-align: right;">Restant</th>
                </tr>
        '''
        for dette in client.dettes:
            dettes_html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 10px;">{dette.description}</td>
                    <td style="padding: 10px; text-align: right;">{dette.montant_dette:.2f} FCFA</td>
                    <td style="padding: 10px; text-align: right; color: #dc3545; font-weight: bold;">{dette.montant_restant:.2f} FCFA</td>
                </tr>
            '''
        dettes_html += f'''
            </table>
            <div style="margin-top: 15px; text-align: right;">
                <strong>Total:</strong> {client.total_restant:.2f} FCFA à payer
            </div>
        </div>
        '''

    msg.html = f'''
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0d6efd; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">SmartCaisse</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; border: 1px solid #dee2e6; border-top: none;">
                    <p>Bonjour <strong>{client.nom}</strong>,</p>
                    <p>Votre profil client a été créé avec succès dans SmartCaisse.</p>
                    {dettes_html}
                    <div style="margin-top: 30px; text-align: center;">
                        <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                            Pour confirmer votre email et automatiser les notifications, cliquez le bouton ci-dessous :
                        </p>
                        <a href="{confirmation_url}" style="display: inline-block; background-color: #0d6efd; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            ✓ Confirmer mon email
                        </a>
                    </div>
                    <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
                        Ce lien expire dans 1 heure.
                    </p>
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Si le bouton ne fonctionne pas, copiez ce lien: <br>
                        <span style="word-break: break-all;">{confirmation_url}</span>
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''

    msg.body = f'''Bonjour {client.nom},

Votre profil client a été créé avec succès dans SmartCaisse.

RÉCAPITULATIF DE VOS DETTES:
Total à payer: {client.total_restant:.2f} FCFA

Pour confirmer votre email et automatiser les notifications, cliquez sur ce lien:
{confirmation_url}

Ce lien expire dans 1 heure.

Cordialement,
L'équipe SmartCaisse
'''

    return _send_email_production(msg)


def send_debt_notification_email(client, dette):
    """
    Envoie une notification au client d'une nouvelle dette créée

    Args:
        client: Objet Client
        dette: Objet Dette créé
    """
    # Mode développement
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 70)
        print('MODE DEVELOPPEMENT - Notification nouvelle dette:')
        print(f'Destinataire: {client.email}')
        print(f'Client: {client.nom}')
        print(f'Description: {dette.description}')
        print(f'Montant: {dette.montant_dette:.2f} FCFA')
        print(f'Statut confirmé: {client.email_confirmed}')
        print('=' * 70 + '\n')
        return True

    msg = Message(
        subject=f'SmartCaisse - Nouvelle dette enregistrée',
        recipients=[client.email]
    )

    msg.html = f'''
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0d6efd; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">SmartCaisse</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; border: 1px solid #dee2e6; border-top: none;">
                    <p>Bonjour <strong>{client.nom}</strong>,</p>
                    <p>Une nouvelle dette a été enregistrée sur votre compte.</p>

                    <div style="margin-top: 20px; background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 3px;">
                        <h3 style="color: #856404; margin-top: 0;">Détails de la dette :</h3>
                        <table style="width: 100%; color: #856404;">
                            <tr>
                                <td style="padding: 8px;"><strong>Description:</strong></td>
                                <td style="padding: 8px; text-align: right;">{dette.description}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;"><strong>Montant:</strong></td>
                                <td style="padding: 8px; text-align: right; font-size: 18px; font-weight: bold;">{dette.montant_dette:.2f} FCFA</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;"><strong>Date:</strong></td>
                                <td style="padding: 8px; text-align: right;">{dette.date.strftime('%d/%m/%Y')}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="margin-top: 20px;">
                        <p style="color: #666; font-size: 14px;">
                            Vous êtes libre de payer cette dette à votre convenance. Chaque paiement effectué sera confirmé par email.
                        </p>
                    </div>

                    <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
                        Merci de votre confiance,<br>
                        L'équipe SmartCaisse
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''

    msg.body = f'''Bonjour {client.nom},

Une nouvelle dette a été enregistrée sur votre compte.

DÉTAILS DE LA DETTE:
Description: {dette.description}
Montant: {dette.montant_dette:.2f} FCFA
Date: {dette.date.strftime('%d/%m/%Y')}

Vous êtes libre de payer cette dette à votre convenance.

Cordialement,
L'équipe SmartCaisse
'''

    return _send_email_production(msg)


def send_payment_confirmation_email(client, paiement, dette):
    """
    Envoie une confirmation de paiement reçu au client

    Args:
        client: Objet Client
        paiement: Objet Paiement créé
        dette: Objet Dette associée
    """
    # Mode développement
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 70)
        print('MODE DEVELOPPEMENT - Confirmation de paiement:')
        print(f'Destinataire: {client.email}')
        print(f'Client: {client.nom}')
        print(f'Montant payé: {paiement.montant:.2f} FCFA')
        print(f'Montant restant: {dette.montant_restant:.2f} FCFA')
        print(f'Dette soldée: {dette.est_soldee}')
        print('=' * 70 + '\n')
        return True

    msg = Message(
        subject=f'SmartCaisse - Paiement confirmé',
        recipients=[client.email]
    )

    # Déterminer la couleur et le message selon le statut
    if dette.est_soldee:
        couleur_statut = '#28a745'
        badge_statut = '✓ Entièrement payée'
        message_statut = '<p style="color: #155724; background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;"><strong>Excellent !</strong> Cette dette est maintenant entièrement payée. Merci !</p>'
    else:
        couleur_statut = '#ffc107'
        badge_statut = '⏱ En cours'
        message_statut = f'<p style="color: #856404; background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;"><strong>Restant à payer:</strong> {dette.montant_restant:.2f} FCFA</p>'

    msg.html = f'''
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0d6efd; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">SmartCaisse</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; border: 1px solid #dee2e6; border-top: none;">
                    <p>Bonjour <strong>{client.nom}</strong>,</p>
                    <p>Nous avons bien reçu votre paiement. Merci !</p>

                    <div style="margin-top: 20px; background-color: #e7f3ff; padding: 15px; border-left: 4px solid #0d6efd; border-radius: 3px;">
                        <h3 style="color: #004085; margin-top: 0;">Détails du paiement :</h3>
                        <table style="width: 100%; color: #004085;">
                            <tr>
                                <td style="padding: 8px;"><strong>Description:</strong></td>
                                <td style="padding: 8px; text-align: right;">{dette.description}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;"><strong>Montant payé:</strong></td>
                                <td style="padding: 8px; text-align: right; font-size: 18px; font-weight: bold; color: #28a745;">{paiement.montant:.2f} FCFA</td>
                            </tr>
                            <tr style="background-color: #fff; border-top: 2px solid #0d6efd;">
                                <td style="padding: 8px;"><strong>Montant initial:</strong></td>
                                <td style="padding: 8px; text-align: right;">{dette.montant_dette:.2f} FCFA</td>
                            </tr>
                            <tr style="background-color: #fff;">
                                <td style="padding: 8px;"><strong>Montant payé au total:</strong></td>
                                <td style="padding: 8px; text-align: right;">{dette.montant_paye:.2f} FCFA ({dette.pourcentage_paye:.0f}%)</td>
                            </tr>
                        </table>
                    </div>

                    {message_statut}

                    <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
                        Merci de votre confiance,<br>
                        L'équipe SmartCaisse
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''

    msg.body = f'''Bonjour {client.nom},

Nous avons bien reçu votre paiement. Merci !

DÉTAILS DU PAIEMENT:
Description: {dette.description}
Montant payé: {paiement.montant:.2f} FCFA
Montant initial: {dette.montant_dette:.2f} FCFA
Montant payé au total: {dette.montant_paye:.2f} FCFA ({dette.pourcentage_paye:.0f}%)

{'Statut: Entièrement payée ✓' if dette.est_soldee else f'Montant restant: {dette.montant_restant:.2f} FCFA'}

Cordialement,
L'équipe SmartCaisse
'''

    return _send_email_production(msg)


def send_invoice_email(invoice, client, user=None):
    """
    Envoie une facture au client par email avec PDF en pièce jointe

    Args:
        invoice: Objet Invoice
        client: Objet Client
        user: Objet User (pour générer le PDF avec infos entreprise)
    """
    # Si pas de client avec email, pas d'envoi
    if not client or not client.email:
        return False

    # Mode développement
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 70)
        print('MODE DEVELOPPEMENT - Envoi facture avec PDF:')
        print(f'Destinataire: {client.email}')
        print(f'Client: {client.nom}')
        print(f'Facture: {invoice.numero}')
        print(f'Total: {invoice.total:.2f} FCFA')
        print(f'PDF attaché: facture_{invoice.numero}.pdf')
        print('=' * 70 + '\n')
        return True

    # Générer le PDF de la facture
    from app.exports.pdf_generator import PDFGenerator
    generator = PDFGenerator(f"Facture {invoice.numero}")
    pdf_buffer = generator.generate_invoice_pdf(invoice, user)

    # Construire le message
    msg = Message(
        subject=f'SmartCaisse - Facture {invoice.numero}',
        recipients=[client.email]
    )

    # Générer liste des articles
    items_html = ''
    for item in invoice.items:
        items_html += f'''
        <tr style="border-bottom: 1px solid #dee2e6;">
            <td style="padding: 10px;">{item.product_name}</td>
            <td style="padding: 10px; text-align: center;">{item.quantity}</td>
            <td style="padding: 10px; text-align: right;">{item.unit_price:.2f} FCFA</td>
            <td style="padding: 10px; text-align: right; font-weight: bold;">{item.total:.2f} FCFA</td>
        </tr>
        '''

    msg.html = f'''
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0d6efd; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">SmartCaisse</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; border: 1px solid #dee2e6; border-top: none;">
                    <p>Bonjour <strong>{client.nom}</strong>,</p>
                    <p>Veuillez trouver ci-jointe votre facture en PDF. Vous pouvez également consulter les détails ci-dessous:</p>

                    <div style="margin-top: 20px; background-color: #fff; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                        <h3 style="color: #0d6efd; margin-top: 0;">Facture #{invoice.numero}</h3>
                        <p><strong>Date:</strong> {invoice.date.strftime('%d/%m/%Y')}</p>

                        <table style="width: 100%; margin-top: 15px; border-collapse: collapse;">
                            <tr style="background-color: #e9ecef; border-bottom: 2px solid #dee2e6;">
                                <th style="padding: 10px; text-align: left;">Article</th>
                                <th style="padding: 10px; text-align: center;">Quantité</th>
                                <th style="padding: 10px; text-align: right;">Prix unitaire</th>
                                <th style="padding: 10px; text-align: right;">Total</th>
                            </tr>
                            {items_html}
                        </table>

                        <div style="margin-top: 20px; text-align: right; padding-top: 15px; border-top: 2px solid #dee2e6;">
                            <h3 style="color: #0d6efd; margin: 10px 0;">Total: {invoice.total:.2f} FCFA</h3>
                        </div>
                    </div>

                    <div style="margin-top: 30px; background-color: #e7f3ff; padding: 15px; border-left: 4px solid #0d6efd; border-radius: 3px;">
                        <p style="margin: 0;"><strong>Modalités de paiement:</strong></p>
                        <p style="margin: 10px 0 0 0; color: #666;">{invoice.notes if invoice.notes else 'À convenir avec le vendeur'}</p>
                    </div>

                    <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
                        Merci de votre confiance,<br>
                        L'équipe SmartCaisse
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''

    msg.body = f'''Bonjour {client.nom},

Veuillez trouver ci-jointe votre facture en PDF.

===============================
FACTURE #{invoice.numero}
Date: {invoice.date.strftime('%d/%m/%Y')}
===============================

'''
    for item in invoice.items:
        msg.body += f'''{item.product_name}
  Quantité: {item.quantity}
  Prix unitaire: {item.unit_price:.2f} FCFA
  Total: {item.total:.2f} FCFA

'''
    msg.body += f'''
===============================
TOTAL: {invoice.total:.2f} FCFA
===============================

Modalités de paiement:
{invoice.notes if invoice.notes else 'À convenir avec le vendeur'}

Merci de votre confiance,
L'équipe SmartCaisse
'''

    # Attacher le PDF
    msg.attach(
        filename=f'facture_{invoice.numero}.pdf',
        content_type='application/pdf',
        data=pdf_buffer.getvalue()
    )

    return _send_email_production(msg)


def _send_email_production(msg):
    """
    Envoie l'email en production avec gestion d'erreurs

    Args:
        msg: Objet Message Flask-Mail

    Returns:
        True si succès, False si erreur
    """
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erreur lors de l\'envoi d\'email: {e}')
        return False





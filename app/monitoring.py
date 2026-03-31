"""
Service de monitoring pour SmartCaisse
- Vérification stock bas
- Envoi d'alertes email
"""
from flask import current_app, render_template
from flask_mail import Message
from app import mail, db
from app.models import Product


def check_low_stock_and_alert():
    """
    Vérifie les produits avec stock bas et envoie une alerte email
    À exécuter quotidiennement (scheduler ou cron)
    
    Critères:
    - Stock <= 5 unités
    - Stock > 0 (pas épuisé complètement)
    
    Returns:
        dict: Résultat avec nombre de produits et statut envoi
    """
    try:
        # Récupérer produits avec stock bas
        low_stock_products = Product.query.filter(
            Product.stock_cache <= 5,
            Product.stock_cache > 0
        ).order_by(Product.stock_cache).all()
        
        if not low_stock_products:
            current_app.logger.info('Stock monitoring: No low stock products')
            return {'products': 0, 'sent': False, 'message': 'Aucun produit en stock bas'}
        
        # Grouper par utilisateur
        by_user = {}
        for product in low_stock_products:
            if product.user_id not in by_user:
                by_user[product.user_id] = []
            by_user[product.user_id].append(product)
        
        # Envoyer email par utilisateur
        sent_count = 0
        for user_id, products in by_user.items():
            # Récupérer l'utilisateur
            from app.models import User
            user = User.query.get(user_id)
            
            if not user or not user.email:
                continue
            
            if send_low_stock_alert_email(user, products):
                sent_count += 1
                current_app.logger.info(f'Low stock alert sent to user {user.id}: {len(products)} products')
        
        return {
            'products': len(low_stock_products),
            'users': len(by_user),
            'sent': sent_count,
            'message': f'{len(low_stock_products)} produits en stock bas, {sent_count} alertes envoyées'
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in stock monitoring: {e}')
        return {'error': str(e)}


def send_low_stock_alert_email(user, products):
    """
    Envoie un email d'alerte stock bas à un utilisateur
    
    Args:
        user: Objet User
        products: Liste de produits en stock bas
        
    Returns:
        bool: True si envoi réussi
    """
    # Mode développement: affichage console
    if not current_app.config.get('MAIL_USERNAME'):
        print('\n' + '=' * 70)
        print('MODE DEVELOPPEMENT - Alerte Stock Bas:')
        print(f'Destinataire: {user.email}')
        print(f'Utilisateur: {user.username}')
        print(f'Nombre de produits: {len(products)}')
        print('Produits:')
        for p in products:
            print(f'  - {p.name}: {p.stock_cache} unités (SKU: {p.sku or "N/A"})')
        print('=' * 70 + '\n')
        return True
    
    try:
        msg = Message(
            subject=f'⚠️ Alerte Stock Bas - {len(products)} produit(s)',
            recipients=[user.email]
        )
        
        # Construction du tableau HTML
        products_html = ''
        for product in products:
            # Badge couleur selon niveau stock
            if product.stock_cache == 0:
                badge_class = 'danger'
                badge_text = 'ÉPUISÉ'
            elif product.stock_cache <= 2:
                badge_class = 'danger'
                badge_text = 'CRITIQUE'
            elif product.stock_cache <= 5:
                badge_class = 'warning'
                badge_text = 'BAS'
            else:
                badge_class = 'info'
                badge_text = 'NORMAL'
            
            category_name = product.category.name if product.category else 'Sans catégorie'
            
            products_html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 10px;">{product.name}</td>
                    <td style="padding: 10px;">{product.sku or 'N/A'}</td>
                    <td style="padding: 10px;">{category_name}</td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="background-color: #{"dc3545" if badge_class == "danger" else "ffc107"}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">
                            {product.stock_cache}
                        </span>
                    </td>
                    <td style="padding: 10px; text-align: right;">{product.price:.2f} FCFA</td>
                </tr>
            '''
        
        msg.html = f'''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 800px; margin: 0 auto;">
                    <div style="background-color: #ffc107; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                        <h1 style="color: #333; margin: 0;">⚠️ Alerte Stock Bas</h1>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; border: 1px solid #dee2e6; border-top: none;">
                        <p>Bonjour <strong>{user.username}</strong>,</p>
                        <p style="font-size: 16px; color: #856404;">
                            <strong>{len(products)} produit(s)</strong> ont un stock bas ou épuisé dans votre inventaire.
                        </p>
                        
                        <div style="margin-top: 20px; background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="background-color: #e9ecef; border-bottom: 2px solid #dee2e6;">
                                        <th style="padding: 10px; text-align: left;">Produit</th>
                                        <th style="padding: 10px; text-align: left;">SKU</th>
                                        <th style="padding: 10px; text-align: left;">Catégorie</th>
                                        <th style="padding: 10px; text-align: center;">Stock</th>
                                        <th style="padding: 10px; text-align: right;">Prix</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products_html}
                                </tbody>
                            </table>
                        </div>
                        
                        <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 3px;">
                            <p style="margin: 0; color: #856404;">
                                <strong>Action recommandée:</strong> Réapprovisionner ces produits pour éviter les ruptures de stock.
                            </p>
                        </div>
                        
                        <div style="margin-top: 30px; text-align: center;">
                            <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/inventory" 
                               style="display: inline-block; background-color: #0d6efd; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                📦 Voir l'inventaire
                            </a>
                        </div>
                        
                        <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
                            Cette alerte est envoyée quotidiennement pour les produits avec stock ≤ 5 unités.<br>
                            SmartCaisse - Gestion Intelligente
                        </p>
                    </div>
                </div>
            </body>
        </html>
        '''
        
        msg.body = f'''Bonjour {user.username},

{len(products)} produit(s) ont un stock bas ou épuisé dans votre inventaire:

'''
        for product in products:
            msg.body += f'- {product.name} (SKU: {product.sku or "N/A"}): {product.stock_cache} unités\n'
        
        msg.body += '''
Action recommandée: Réapprovisionner ces produits pour éviter les ruptures de stock.

Connectez-vous à SmartCaisse pour gérer votre inventaire.

Cordialement,
L'équipe SmartCaisse
'''
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f'Failed to send low stock alert to {user.email}: {e}')
        return False


def get_low_stock_summary():
    """
    Récupère un résumé du stock bas pour dashboard
    
    Returns:
        dict: Statistiques stock bas
    """
    try:
        low_stock = Product.query.filter(
            Product.stock_cache <= 5,
            Product.stock_cache > 0
        ).count()
        
        out_of_stock = Product.query.filter(
            Product.stock_cache == 0
        ).count()
        
        return {
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_alerts': low_stock + out_of_stock
        }
    except Exception as e:
        current_app.logger.error(f'Error getting stock summary: {e}')
        return {'low_stock': 0, 'out_of_stock': 0, 'total_alerts': 0}

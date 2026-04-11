"""
Point d'entrée de l'application SmartCaisse
Exécuter avec: python run.py
"""
import os
from app import create_app

# Création de l'instance de l'application
app = create_app()

if __name__ == '__main__':
    # Debug mode contrôlé par FLASK_ENV
    # En développement: FLASK_ENV=development
    # En production: FLASK_ENV=production
    # En production, utiliser un serveur WSGI comme Gunicorn
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)

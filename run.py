"""
Point d'entrée de l'application SmartCaisse
Exécuter avec: python run.py
"""
from app import create_app

# Création de l'instance de l'application
app = create_app()

if __name__ == '__main__':
    # Mode debug activé pour le développement
    # En production, utiliser un serveur WSGI comme Gunicorn
    app.run(debug=True, host='127.0.0.1', port=5000)

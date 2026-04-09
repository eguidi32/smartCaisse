"""
Entry point WSGI pour PythonAnywhere
"""
import os
import sys

# Ajouter le répertoire du projet au path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(os.path.join(project_dir, '.env'))

# Créer l'application
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()

# SmartCaisse

Application web de gestion des recettes et depenses pour petits commercants.

## Fonctionnalites

- Gestion des transactions (recettes/depenses)
- Tableau de bord avec statistiques
- Gestion des dettes clients
- Export PDF et CSV
- Systeme multi-utilisateurs avec roles (admin/user)
- Envoi d'emails (reinitialisation mot de passe, creation compte)

## Technologies

- **Backend:** Flask (Python)
- **Base de donnees:** SQLite
- **Frontend:** Bootstrap 5
- **Email:** Flask-Mail (SMTP Gmail)

## Installation locale

```bash
# Cloner le projet
git clone https://github.com/eguidi32/smartCaisse.git
cd smartCaisse

# Creer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dependances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec vos valeurs

# Lancer l'application
python run.py
```

## Configuration

Copiez `.env.example` en `.env` et configurez :

```
SECRET_KEY=votre-cle-secrete
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-application
```

## Auteur

NOUR BRAHIM

## Licence

MIT

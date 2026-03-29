"""
Script pour créer le premier utilisateur administrateur
Exécuter une seule fois: python create_admin.py
"""
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Vérifier si un admin existe déjà
    admin = User.query.filter_by(role='admin').first()

    if admin:
        print(f"Un administrateur existe déjà: {admin.username} ({admin.email})")
    else:
        # Créer le premier admin
        admin = User(
            username='admin',
            email='admin@smartcaisse.local',
            role='admin',
            is_active=True,
            must_change_password=True  # Forcer le changement au premier login
        )
        admin.set_password('admin123')  # Mot de passe temporaire

        db.session.add(admin)
        db.session.commit()

        print("=" * 50)
        print("ADMINISTRATEUR CRÉÉ AVEC SUCCÈS")
        print("=" * 50)
        print(f"Email: admin@smartcaisse.local")
        print(f"Mot de passe: admin123")
        print("")
        print("IMPORTANT: Changez ce mot de passe après la première connexion!")
        print("=" * 50)

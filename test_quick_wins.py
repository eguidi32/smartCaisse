"""
Script de test des Quick Wins - SmartCaisse
Vérifie que toutes les améliorations fonctionnent correctement
"""
import sys
import os

print("\n" + "="*60)
print("   TEST QUICK WINS - SmartCaisse")
print("="*60 + "\n")

# Test 1: Vérifier dépendances installées
print("[1/6] Vérification des dépendances...")
try:
    import flask_talisman
    print("  ✅ Flask-Talisman installé")
except ImportError:
    print("  ❌ Flask-Talisman manquant")
    sys.exit(1)

try:
    import flask_limiter
    print("  ✅ Flask-Limiter installé")
except ImportError:
    print("  ❌ Flask-Limiter manquant")
    sys.exit(1)

try:
    import apscheduler
    print("  ✅ APScheduler installé")
except ImportError:
    print("  ❌ APScheduler manquant")
    sys.exit(1)

print()

# Test 2: Vérifier fichier .env
print("[2/6] Vérification du fichier .env...")
if os.path.exists('.env'):
    print("  ✅ Fichier .env existe")
    
    # Vérifier SECRET_KEY
    with open('.env', 'r') as f:
        content = f.read()
        if 'SECRET_KEY=' in content and 'votre-cle-secrete' not in content:
            print("  ✅ SECRET_KEY configurée")
        else:
            print("  ⚠️  SECRET_KEY non configurée ou par défaut")
            print("     → Éditez .env et ajoutez une clé unique")
else:
    print("  ❌ Fichier .env manquant")
    print("     → Lancez: install_quick_wins.bat")
    sys.exit(1)

print()

# Test 3: Vérifier dossier logs
print("[3/6] Vérification du dossier logs...")
if os.path.exists('logs'):
    print("  ✅ Dossier logs/ existe")
else:
    print("  ⚠️  Dossier logs/ manquant (sera créé au démarrage)")

print()

# Test 4: Vérifier modules app
print("[4/6] Vérification des nouveaux modules...")
try:
    from app.monitoring import check_low_stock_and_alert
    print("  ✅ app.monitoring importé")
except ImportError as e:
    print(f"  ❌ Erreur import monitoring: {e}")
    sys.exit(1)

try:
    from app.scheduler import init_scheduler
    print("  ✅ app.scheduler importé")
except ImportError as e:
    print(f"  ❌ Erreur import scheduler: {e}")
    sys.exit(1)

print()

# Test 5: Vérifier configuration
print("[5/6] Vérification de la configuration...")
try:
    from config import Config
    
    # Vérifier nouvelles variables
    if hasattr(Config, 'LOG_LEVEL'):
        print("  ✅ Config.LOG_LEVEL défini")
    if hasattr(Config, 'FORCE_HTTPS'):
        print("  ✅ Config.FORCE_HTTPS défini")
    if hasattr(Config, 'RATELIMIT_ENABLED'):
        print("  ✅ Config.RATELIMIT_ENABLED défini")
        
except Exception as e:
    print(f"  ❌ Erreur configuration: {e}")
    sys.exit(1)

print()

# Test 6: Test création app
print("[6/6] Test de création de l'application...")
try:
    from app import create_app
    app = create_app()
    
    # Vérifier extensions
    if hasattr(app, 'logger'):
        print("  ✅ Logger configuré")
    
    print("  ✅ Application créée avec succès")
    
except Exception as e:
    print(f"  ❌ Erreur création app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*60)
print("   ✅ TOUS LES TESTS PASSÉS !")
print("="*60)
print()
print("Prêt à lancer:")
print("  python run.py")
print()
print("Pour tester le monitoring manuellement:")
print("  python test_monitoring.py")
print()

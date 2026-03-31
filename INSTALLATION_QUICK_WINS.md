# 📦 INSTALLATION - Quick Wins SmartCaisse

## 🚀 COMMANDES D'INSTALLATION

### Option 1: Installation automatique (Recommandé)

```bash
# 1. Installer toutes les nouvelles dépendances
pip install -r requirements.txt

# 2. Créer .env avec SECRET_KEY
cp .env.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
echo "FLASK_ENV=development" >> .env
echo "LOG_LEVEL=INFO" >> .env

# 3. Créer dossier logs
mkdir -p logs

# 4. Tester
python run.py
```

### Option 2: Installation manuelle

```bash
# 1. Installer nouvelles dépendances individuellement
pip install Flask-Talisman==1.1.0
pip install Flask-Limiter==3.5.0
pip install APScheduler==3.10.4

# 2. Créer .env
cp .env.example .env
# Puis éditer .env et ajouter votre SECRET_KEY

# 3. Créer dossier logs
mkdir logs

# 4. Lancer
python run.py
```

---

## ✅ VÉRIFICATION INSTALLATION

### Test 1: Dépendances installées

```bash
python -c "import flask_talisman; print('✅ Talisman OK')"
python -c "import flask_limiter; print('✅ Limiter OK')"
python -c "import apscheduler; print('✅ APScheduler OK')"
```

### Test 2: .env configuré

```bash
# Vérifier .env existe
ls -la .env

# Vérifier SECRET_KEY présent
grep SECRET_KEY .env
```

### Test 3: Logs fonctionnent

```bash
# Lancer app
python run.py

# Dans un autre terminal, vérifier logs
tail -f logs/smartcaisse.log

# Devrait afficher:
# [2026-03-31 ...] INFO in __init__: SmartCaisse startup
```

### Test 4: Rate limiting actif

```bash
# Dans navigateur, aller sur /auth/login
# Tenter 11 connexions rapides
# La 11ème devrait retourner HTTP 429 (Too Many Requests)
```

---

## 🐛 TROUBLESHOOTING

### Erreur: "No module named 'flask_talisman'"

```bash
# Solution
pip install Flask-Talisman==1.1.0
```

### Erreur: "Permission denied: logs/smartcaisse.log"

```bash
# Solution
mkdir logs
chmod 755 logs
```

### Erreur: "SECRET_KEY not found"

```bash
# Vérifier .env
cat .env | grep SECRET_KEY

# Si vide, générer:
python -c "import secrets; print(secrets.token_hex(32))"
# Copier dans .env
```

### Scheduler ne démarre pas

```bash
# Le scheduler est désactivé en mode développement (normal)
# Pour tester, mettre dans .env:
FLASK_ENV=production

# Ou tester manuellement:
python
>>> from app import create_app
>>> from app.scheduler import run_low_stock_check_now
>>> app = create_app()
>>> result = run_low_stock_check_now(app)
>>> print(result)
```

---

## 📝 CHANGELOG

### Fichiers modifiés:
- ✅ `requirements.txt` - 3 nouvelles dépendances
- ✅ `config.py` - Nouvelles variables configuration
- ✅ `app/__init__.py` - Setup logging, Talisman, Limiter, Scheduler
- ✅ `app/routes/auth.py` - Rate limiting + logs
- ✅ `.env.example` - Documentation améliorée

### Fichiers créés:
- ✅ `app/monitoring.py` - Service monitoring stock
- ✅ `app/scheduler.py` - Tâches planifiées
- ✅ `SECURITY_SETUP.md` - Guide sécurité
- ✅ `logs/` - Dossier logs (à créer)

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Installer dépendances
2. ✅ Configurer .env
3. ✅ Créer dossier logs
4. ✅ Tester en local
5. ⚪ Déployer sur PythonAnywhere
6. ⚪ Surveiller logs/smartcaisse.log

---

**Date:** 31 mars 2026  
**Version:** 2.1 (Quick Wins)

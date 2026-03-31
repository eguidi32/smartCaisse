# 🚨 DÉPLOIEMENT PRODUCTION - Quick Wins SmartCaisse

**ATTENTION:** Le site est déjà en ligne. Cette procédure minimise les risques.

---

## ⚠️ PRINCIPES DE SÉCURITÉ

1. **TOUJOURS tester en local d'abord**
2. **TOUJOURS faire un backup avant**
3. **Déployer pendant heures creuses**
4. **Avoir un plan de rollback**
5. **Tester après chaque étape**

---

## 📋 PLAN DE DÉPLOIEMENT

### Phase 1: PRÉPARATION (Local - 30 min)
- Tester les changements en local
- Vérifier que tout fonctionne
- Lister les changements exacts

### Phase 2: BACKUP (Production - 5 min)
- Sauvegarder la base de données
- Sauvegarder le code actuel
- Noter la version actuelle

### Phase 3: DÉPLOIEMENT (Production - 10 min)
- Pull des nouveaux changements
- Installer dépendances
- Configurer .env
- Reload application

### Phase 4: VÉRIFICATION (Production - 10 min)
- Tester login/logout
- Vérifier logs
- Tester features principales

### Phase 5: ROLLBACK si problème (5 min)
- Restaurer code précédent
- Restaurer base de données
- Reload application

**Temps total:** ~1 heure (downtime: <2 minutes)

---

## 🔧 PHASE 1: PRÉPARATION (LOCAL)

### Étape 1.1: Cloner en local (si pas déjà fait)

```bash
# Sur votre machine locale
cd C:\Users\user\Desktop
git clone <votre-repo-github> smartcaisse-test
cd smartcaisse-test
```

### Étape 1.2: Installer dépendances en local

```bash
# Créer environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer TOUTES les dépendances (anciennes + nouvelles)
pip install -r requirements.txt
```

### Étape 1.3: Configurer .env local

```bash
# Copier exemple
copy .env.example .env

# Générer SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Éditer .env et ajouter:
# SECRET_KEY=<clé-générée>
# FLASK_ENV=development
```

### Étape 1.4: Créer dossier logs

```bash
mkdir logs
```

### Étape 1.5: Tester en local

```bash
# Lancer l'application
python run.py

# Dans navigateur: http://localhost:5000
# Tester:
# - Login/logout
# - Créer un produit
# - Voir logs\smartcaisse.log
```

### Étape 1.6: Test de charge (rate limiting)

```bash
# Tenter 11 connexions rapides
# La 11ème doit retourner "Too Many Requests"
```

### ✅ VALIDATION PHASE 1

- [ ] App démarre sans erreur en local
- [ ] Login fonctionne
- [ ] Logs créés dans logs\smartcaisse.log
- [ ] Rate limiting actif (429 après 10 tentatives)
- [ ] Aucune erreur dans logs

**SI TOUT OK → Passer Phase 2**  
**SI PROBLÈME → Débugger avant de toucher production**

---

## 💾 PHASE 2: BACKUP (PRODUCTION)

### Étape 2.1: Connexion au serveur

**PythonAnywhere:**
```bash
# Ouvrir un Bash console sur PythonAnywhere
# https://www.pythonanywhere.com/user/<username>/consoles/
```

### Étape 2.2: Aller dans le projet

```bash
cd ~/smartcaisse  # ou le nom de votre dossier
pwd  # Vérifier le chemin
```

### Étape 2.3: Backup base de données

```bash
# Créer dossier backups
mkdir -p backups

# Backup DB avec timestamp
cp instance/smartcaisse.db backups/smartcaisse_$(date +%Y%m%d_%H%M%S).db

# Vérifier
ls -lh backups/
```

### Étape 2.4: Backup code

```bash
# Créer tag git (recommandé)
git tag -a v2.0-before-quickwins -m "Before Quick Wins deployment"
git push origin v2.0-before-quickwins

# OU créer une copie locale
cd ..
cp -r smartcaisse smartcaisse_backup_$(date +%Y%m%d)
```

### Étape 2.5: Noter l'état actuel

```bash
# Voir commit actuel
git log -1

# Voir dépendances installées
pip list | grep -E "Flask-Talisman|Flask-Limiter|APScheduler"

# Noter si absentes (normal)
```

### ✅ VALIDATION PHASE 2

- [ ] Backup DB créé (vérifier taille > 0)
- [ ] Tag git créé OU copie code faite
- [ ] Chemin backup noté quelque part

---

## 🚀 PHASE 3: DÉPLOIEMENT (PRODUCTION)

### ⚠️ IMPORTANT
**À partir d'ici, le site peut avoir de petites interruptions.**  
**Faites ça pendant heures creuses (nuit/tôt matin)**

### Étape 3.1: Pull derniers changements

```bash
cd ~/smartcaisse

# Vérifier statut git
git status

# Stash changements locaux si nécessaire
git stash

# Pull
git pull origin main  # ou master selon votre branche

# Vérifier nouveaux fichiers
ls -la app/monitoring.py
ls -la app/scheduler.py
```

### Étape 3.2: Installer nouvelles dépendances

```bash
# IMPORTANT: Utiliser --user sur PythonAnywhere
pip install --user Flask-Talisman==1.1.0
pip install --user Flask-Limiter==3.5.0
pip install --user APScheduler==3.10.4

# Vérifier installation
pip list | grep -E "Flask-Talisman|Flask-Limiter|APScheduler"
```

### Étape 3.3: Créer dossier logs

```bash
mkdir -p logs
chmod 755 logs
```

### Étape 3.4: Configurer .env

```bash
# Vérifier .env existe
ls -la .env

# Si .env n'existe pas:
cp .env.example .env

# Éditer .env
nano .env

# Ajouter/Modifier:
SECRET_KEY=<générer-une-clé-unique>
FLASK_ENV=production
LOG_LEVEL=INFO
LOG_FILE=logs/smartcaisse.log

# Pour générer SECRET_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copier la clé générée dans .env
# Ctrl+X, Y, Enter pour sauvegarder
```

### Étape 3.5: Reload l'application

**PythonAnywhere:**
1. Aller sur Web tab
2. Trouver votre app (smartcaisse.pythonanywhere.com ou autre)
3. Cliquer **"Reload"** (gros bouton vert)
4. Attendre 10-15 secondes

**OU en ligne de commande:**
```bash
touch /var/www/<username>_pythonanywhere_com_wsgi.py
```

### Étape 3.6: Vérifier démarrage

```bash
# Vérifier logs d'erreur PythonAnywhere
# Web tab → Error log (lien en bas)

# OU en bash:
tail -50 /var/log/<username>.pythonanywhere.com.error.log
```

---

## ✅ PHASE 4: VÉRIFICATION (PRODUCTION)

### Étape 4.1: Test basique site

```bash
# Dans navigateur, aller sur votre site
https://<username>.pythonanywhere.com/auth/login

# Tester:
1. Page charge normalement ✓
2. Login fonctionne ✓
3. Dashboard s'affiche ✓
4. Créer un produit test ✓
5. Voir l'inventaire ✓
```

### Étape 4.2: Vérifier logs application

```bash
cd ~/smartcaisse

# Voir logs SmartCaisse
tail -50 logs/smartcaisse.log

# Devrait contenir:
# [timestamp] INFO in __init__: SmartCaisse startup
# [timestamp] INFO in __init__: Database tables created/verified
```

### Étape 4.3: Test rate limiting

```bash
# Tentez 11 logins rapides
# La 11ème devrait afficher "Too Many Requests"
```

### Étape 4.4: Test monitoring (optionnel)

```bash
cd ~/smartcaisse

# Lancer test monitoring
python3 test_monitoring.py

# Devrait afficher résumé stock
```

### ✅ VALIDATION PHASE 4

- [ ] Site accessible
- [ ] Login/logout fonctionnel
- [ ] Pas d'erreur 500
- [ ] Logs créés
- [ ] Rate limiting actif
- [ ] Toutes features marchent

**SI TOUT OK → SUCCÈS ! 🎉**  
**SI PROBLÈME → Phase 5 (Rollback)**

---

## 🔙 PHASE 5: ROLLBACK (Si problème)

### Étape 5.1: Restaurer code

```bash
cd ~/smartcaisse

# Retour au commit précédent
git reset --hard <commit-avant>

# OU
git checkout v2.0-before-quickwins

# Reload
# (Web tab → Reload)
```

### Étape 5.2: Restaurer DB (si nécessaire)

```bash
# Seulement si DB corrompue
cp backups/smartcaisse_YYYYMMDD_HHMMSS.db instance/smartcaisse.db
```

### Étape 5.3: Désinstaller dépendances (optionnel)

```bash
pip uninstall Flask-Talisman Flask-Limiter APScheduler
```

### Étape 5.4: Reload final

```bash
# Reload webapp
# Vérifier site fonctionne comme avant
```

---

## 📊 CHECKLIST COMPLÈTE

### Avant déploiement:
- [ ] Code testé en local
- [ ] Backup DB fait
- [ ] Backup code fait (tag git)
- [ ] Heure creuse choisie
- [ ] Plan de rollback noté

### Pendant déploiement:
- [ ] git pull réussi
- [ ] Dépendances installées
- [ ] .env configuré avec SECRET_KEY unique
- [ ] logs/ créé
- [ ] Webapp reloadée

### Après déploiement:
- [ ] Site accessible
- [ ] Login fonctionne
- [ ] Logs créés
- [ ] Rate limiting actif
- [ ] Pas d'erreur dans logs
- [ ] Features principales testées

---

## 🆘 PROBLÈMES COURANTS

### 1. Erreur 502 Bad Gateway

**Cause:** App crash au démarrage  
**Solution:**
```bash
# Voir error log
tail -100 /var/log/<username>.pythonanywhere.com.error.log

# Vérifier import
python3 -c "from app import create_app; app = create_app()"
```

### 2. ImportError: No module named 'flask_talisman'

**Cause:** Dépendance non installée  
**Solution:**
```bash
pip install --user Flask-Talisman==1.1.0
```

### 3. SECRET_KEY warning

**Cause:** .env mal configuré  
**Solution:**
```bash
nano .env
# Vérifier SECRET_KEY présente et unique
```

### 4. Logs non créés

**Cause:** Permission dossier  
**Solution:**
```bash
mkdir -p logs
chmod 755 logs
```

---

## 📞 SUPPORT

Si problème pendant déploiement:

1. **NE PAS PANIQUER**
2. Noter l'erreur exacte
3. Faire rollback Phase 5
4. Analyser logs en local
5. Corriger et retester local
6. Réessayer déploiement

---

## ✅ SUCCÈS !

Une fois tout validé:

1. Supprimer temp_key.txt (local)
2. Surveiller logs/smartcaisse.log (quelques jours)
3. Tester emails si configurés
4. Profiter des améliorations ! 🎉

**Nouvelles features actives:**
- ✅ HTTPS enforcement (si production)
- ✅ Rate limiting anti-brute-force
- ✅ Logs structurés
- ✅ Monitoring stock quotidien (9h)

---

**Temps estimé total:** 1h  
**Downtime:** <2 minutes  
**Risque:** FAIBLE (rollback possible)

---

**Date:** 31 mars 2026  
**Version:** 2.1 - Quick Wins Production

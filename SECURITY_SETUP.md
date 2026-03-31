# 🔒 CONFIGURATION SÉCURITÉ - SmartCaisse

## ⚠️ AVANT DE DÉPLOYER EN PRODUCTION

### 1. Générer SECRET_KEY unique (OBLIGATOIRE)

```bash
# Générer une clé sécurisée
python -c "import secrets; print(secrets.token_hex(32))"

# Résultat exemple:
# a3f8b2e1c9d4f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
```

**Ajouter dans `.env`:**
```bash
SECRET_KEY=a3f8b2e1c9d4f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
```

### 2. Configurer Email (optionnel mais recommandé)

**Gmail App Password:**
1. Activer 2FA sur votre compte Gmail
2. Aller dans: Compte Google → Sécurité → Mots de passe d'application
3. Générer un mot de passe pour "Autre (nom personnalisé)"
4. Copier le mot de passe (16 caractères)

**Ajouter dans `.env`:**
```bash
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop  # App password (16 chars)
MAIL_DEFAULT_SENDER=SmartCaisse <votre-email@gmail.com>
```

### 3. Mode Production

**Ajouter dans `.env`:**
```bash
FLASK_ENV=production
```

### 4. Vérifier .gitignore

Assurez-vous que `.env` est dans `.gitignore`:
```bash
# Vérifier
cat .gitignore | grep .env

# Devrait afficher:
# .env
```

---

## ✅ CHECKLIST SÉCURITÉ

- [ ] SECRET_KEY unique générée ✅
- [ ] SECRET_KEY ajoutée dans .env ✅
- [ ] FLASK_ENV=production dans .env ✅
- [ ] MAIL_PASSWORD configuré (si emails souhaités) ⚪
- [ ] .env dans .gitignore ✅
- [ ] Fichier .env JAMAIS commité sur Git ✅
- [ ] Admin créé avec `python create_admin.py` ⚪
- [ ] Password admin changé après première connexion ⚪

---

## 🚀 DÉPLOIEMENT

### Local (Développement)
```bash
# 1. Copier .env.example
cp .env.example .env

# 2. Éditer .env avec vos valeurs
nano .env

# 3. Créer admin
python create_admin.py

# 4. Lancer
python run.py
```

### PythonAnywhere (Production)
```bash
# 1. Créer .env sur le serveur
nano /home/USERNAME/smartcaisse/.env

# 2. Ajouter:
SECRET_KEY=<votre-clé-générée>
FLASK_ENV=production
MAIL_USERNAME=...
MAIL_PASSWORD=...

# 3. Créer admin
python create_admin.py

# 4. Reload webapp dans dashboard PythonAnywhere
```

---

## 🔐 BONNES PRATIQUES

### ✅ À FAIRE
- Générer SECRET_KEY unique par environnement (dev, staging, prod)
- Changer password admin par défaut (admin123)
- Utiliser HTTPS en production
- Sauvegarder .env de manière sécurisée (gestionnaire de mots de passe)
- Rotation SECRET_KEY tous les 6-12 mois (invalide sessions)

### ❌ À NE PAS FAIRE
- Commiter .env sur Git
- Réutiliser même SECRET_KEY sur plusieurs projets
- Partager .env par email/chat
- Utiliser clés faibles (< 32 caractères)
- Laisser FLASK_ENV=development en production

---

## 🆘 EN CAS DE COMPROMISSION

Si SECRET_KEY est exposée:

1. **Générer nouvelle clé immédiatement**
2. **Mettre à jour .env**
3. **Redémarrer application**
4. **Invalider toutes les sessions** (utilisateurs devront se reconnecter)
5. **Réinitialiser tokens password reset en cours**

---

**Dernière mise à jour:** 31 mars 2026  
**Version:** 2.0

# Deploiement SmartCaisse sur Oracle Cloud Always Free

Ce guide cible une VM Ubuntu Oracle Cloud avec Nginx + Gunicorn + SQLite.
Pour SmartCaisse, c'est le chemin le plus simple: la base SQLite reste sur le
disque de la VM, et l'application tourne comme un service Linux.

## 1. Creer la VM Oracle

Dans Oracle Cloud Console:

- Compute > Instances > Create instance
- Image: Ubuntu, marquee "Always Free Eligible"
- Shape recommande: `VM.Standard.A1.Flex`, 1 OCPU et 6 GB RAM minimum
- Boot volume: 50 GB
- Ajouter votre cle SSH
- Ouvrir les ports 22, 80 et 443 dans le Security List ou Network Security Group

Si Oracle affiche `out of host capacity`, reessayer plus tard ou dans un autre
Availability Domain de la meme region.

## 2. Installer le serveur

Connexion SSH:

```bash
ssh ubuntu@VOTRE_IP_PUBLIQUE
```

Paquets systeme:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git sqlite3 certbot python3-certbot-nginx
```

Code applicatif:

```bash
sudo mkdir -p /opt/smartcaisse
sudo chown -R ubuntu:www-data /opt/smartcaisse
git clone https://github.com/eguidi32/smartCaisse.git /opt/smartcaisse
cd /opt/smartcaisse
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Configuration:

```bash
cp deploy/oracle/env.production.example .env
python -c "import secrets; print(secrets.token_hex(32))"
nano .env
mkdir -p instance logs backups
```

Dans `.env`, remplacer `SECRET_KEY`, `BASE_URL` et les valeurs email.
Au debut, garder `FORCE_HTTPS=false`. Apres installation du certificat SSL,
mettre `FORCE_HTTPS=true`.

## 3. Recuperer ou creer la base SQLite

Si vous avez deja une base locale:

```bash
scp instance/smartcaisse.db ubuntu@VOTRE_IP_PUBLIQUE:/tmp/smartcaisse.db
sudo mv /tmp/smartcaisse.db /opt/smartcaisse/instance/smartcaisse.db
sudo chown ubuntu:www-data /opt/smartcaisse/instance/smartcaisse.db
sudo chmod 660 /opt/smartcaisse/instance/smartcaisse.db
```

Si c'est une nouvelle installation:

```bash
python create_admin.py
```

Verifier que l'application charge:

```bash
python -m compileall app config.py wsgi.py
```

## 4. Installer Gunicorn comme service

Le service fourni utilise 1 worker + 4 threads, un choix simple et stable pour
SQLite sur une petite application.

```bash
sudo cp deploy/oracle/smartcaisse.service /etc/systemd/system/smartcaisse.service
sudo systemctl daemon-reload
sudo systemctl enable --now smartcaisse
sudo systemctl status smartcaisse
```

Logs:

```bash
sudo journalctl -u smartcaisse -f
```

## 5. Configurer Nginx

```bash
sudo cp deploy/oracle/nginx-smartcaisse.conf /etc/nginx/sites-available/smartcaisse
sudo ln -s /etc/nginx/sites-available/smartcaisse /etc/nginx/sites-enabled/smartcaisse
sudo nginx -t
sudo systemctl reload nginx
```

Tester dans le navigateur:

```text
http://VOTRE_IP_PUBLIQUE
```

## 6. Activer le domaine et HTTPS

Pointer le domaine vers l'IP publique Oracle avec un enregistrement DNS `A`.
Ensuite:

```bash
sudo certbot --nginx -d votre-domaine.com
nano .env
sudo systemctl restart smartcaisse
```

Dans `.env`, mettre:

```text
BASE_URL=https://votre-domaine.com
FORCE_HTTPS=true
```

## 7. Sauvegarder la base

SQLite fonctionne bien pour un petit deploiement, mais il faut sauvegarder:

```bash
sqlite3 /opt/smartcaisse/instance/smartcaisse.db ".backup '/opt/smartcaisse/backups/smartcaisse-backup.db'"
```

Pour recuperer une sauvegarde:

```bash
scp ubuntu@VOTRE_IP_PUBLIQUE:/opt/smartcaisse/backups/smartcaisse-backup.db .
```

## 8. Mise a jour de l'application

```bash
cd /opt/smartcaisse
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart smartcaisse
```

## Checklist finale

- `http://IP` fonctionne avant HTTPS
- `https://domaine` fonctionne apres Certbot
- Connexion admin OK
- Creation utilisateur boutiquier OK
- Creation client par boutiquier OK
- Creation et PDF facture OK
- Suppression client/utilisateur OK
- Sauvegarde SQLite testee

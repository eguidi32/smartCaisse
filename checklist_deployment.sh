#!/bin/bash
# ============================================
# CHECKLIST DÉPLOIEMENT PRODUCTION
# SmartCaisse Quick Wins
# ============================================

echo "=========================================="
echo "  CHECKLIST DÉPLOIEMENT - SmartCaisse"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
CHECKED=0
TOTAL=0

check_item() {
    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] $1... "
    read -p "(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✓ OK${NC}"
        CHECKED=$((CHECKED + 1))
    else
        echo -e "${RED}✗ À FAIRE${NC}"
    fi
    echo
}

echo "=== PHASE 1: PRÉPARATION LOCALE ==="
echo ""

check_item "Code testé en local (python run.py)"
check_item "Login/logout fonctionnel"
check_item "Dépendances installées localement"
check_item "Logs créés dans logs/"
check_item "Rate limiting testé (11 logins)"

echo ""
echo "=== PHASE 2: BACKUP PRODUCTION ==="
echo ""

check_item "Backup DB créé (instance/smartcaisse.db)"
check_item "Tag git créé ou code copié"
check_item "Chemin backup noté"

echo ""
echo "=== PHASE 3: DÉPLOIEMENT ==="
echo ""

check_item "git pull réussi"
check_item "Flask-Talisman installé"
check_item "Flask-Limiter installé"
check_item "APScheduler installé"
check_item "Dossier logs/ créé"
check_item "SECRET_KEY unique générée"
check_item ".env configuré"
check_item "Webapp reloadée"

echo ""
echo "=== PHASE 4: VÉRIFICATION ==="
echo ""

check_item "Site accessible"
check_item "Login fonctionne"
check_item "Dashboard affiche"
check_item "Créer produit fonctionne"
check_item "Fichier logs/smartcaisse.log existe"
check_item "Logs contiennent 'SmartCaisse startup'"
check_item "Rate limiting actif (429 après 10 logins)"
check_item "Pas d'erreur 500"

echo ""
echo "=========================================="
echo "  RÉSULTAT: $CHECKED/$TOTAL items validés"
echo "=========================================="
echo ""

if [ $CHECKED -eq $TOTAL ]; then
    echo -e "${GREEN}✅ DÉPLOIEMENT RÉUSSI !${NC}"
    echo ""
    echo "Prochaines étapes:"
    echo "  1. Surveiller logs pendant 24h"
    echo "  2. Tester emails si configurés"
    echo "  3. Supprimer temp_key.txt"
    echo ""
else
    echo -e "${YELLOW}⚠️  $((TOTAL - CHECKED)) items non validés${NC}"
    echo ""
    echo "Actions:"
    echo "  1. Corriger les items marqués ✗"
    echo "  2. Relancer cette checklist"
    echo "  3. Si bloqué: voir DEPLOIEMENT_PRODUCTION.md"
    echo ""
fi

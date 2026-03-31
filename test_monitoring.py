"""
Test manuel du monitoring de stock - SmartCaisse
"""
from app import create_app
from app.monitoring import check_low_stock_and_alert, get_low_stock_summary

print("\n" + "="*70)
print("   TEST MONITORING STOCK - SmartCaisse")
print("="*70 + "\n")

app = create_app()

with app.app_context():
    # Test 1: Résumé stock
    print("[1/2] Récupération du résumé stock...")
    summary = get_low_stock_summary()
    print(f"  Stock bas (≤5): {summary['low_stock']} produits")
    print(f"  Stock épuisé (0): {summary['out_of_stock']} produits")
    print(f"  Total alertes: {summary['total_alerts']} produits")
    print()
    
    # Test 2: Vérification et envoi alertes
    print("[2/2] Vérification stock et génération alertes...")
    result = check_low_stock_and_alert()
    
    if 'error' in result:
        print(f"  ❌ Erreur: {result['error']}")
    else:
        print(f"  ✅ {result['message']}")
        if 'products' in result:
            print(f"     Produits concernés: {result['products']}")
        if 'users' in result:
            print(f"     Utilisateurs notifiés: {result['users']}")
        if 'sent' in result:
            print(f"     Emails envoyés: {result['sent']}")

print()
print("="*70)
print("Mode développement: Les emails s'affichent dans la console")
print("="*70)
print()

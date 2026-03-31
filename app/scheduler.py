"""
Tâches planifiées pour SmartCaisse
- Monitoring stock bas (quotidien)
- Nettoyage sessions expirées
- Autres tâches périodiques
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import atexit


def init_scheduler(app):
    """
    Initialise le scheduler pour les tâches périodiques
    
    Args:
        app: Instance Flask app
    """
    scheduler = BackgroundScheduler()
    
    # Tâche: Vérifier stock bas tous les jours à 9h
    scheduler.add_job(
        func=check_low_stock_task,
        trigger=CronTrigger(hour=9, minute=0),  # 9h00 chaque jour
        id='check_low_stock',
        name='Vérifier stock bas et envoyer alertes',
        replace_existing=True,
        args=[app]
    )
    
    # TODO: Ajouter d'autres tâches planifiées ici
    # Exemples:
    # - Nettoyage sessions expirées (hebdomadaire)
    # - Backup base de données (quotidien)
    # - Génération rapports mensuels (1er du mois)
    
    # Démarrer le scheduler
    scheduler.start()
    app.logger.info('Scheduler started - Tasks: check_low_stock (daily 9h)')
    
    # Arrêter proprement à la fermeture de l'app
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler


def check_low_stock_task(app):
    """
    Tâche planifiée: Vérifier stock bas et envoyer alertes
    """
    with app.app_context():
        from app.monitoring import check_low_stock_and_alert
        
        app.logger.info('Running scheduled task: check_low_stock')
        result = check_low_stock_and_alert()
        
        if 'error' in result:
            app.logger.error(f'Low stock check failed: {result["error"]}')
        else:
            app.logger.info(f'Low stock check completed: {result["message"]}')


# Pour tester manuellement:
def run_low_stock_check_now(app):
    """
    Exécute la vérification stock bas immédiatement (pour tests)
    
    Usage dans Flask shell:
        from app.scheduler import run_low_stock_check_now
        from app import create_app
        app = create_app()
        run_low_stock_check_now(app)
    """
    with app.app_context():
        from app.monitoring import check_low_stock_and_alert
        return check_low_stock_and_alert()

"""
Routes principales (accueil, dashboard, statistiques)
"""
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from calendar import monthrange
from app import db
from app.models import Transaction

# Création du Blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Tableau de bord principal
    Affiche les totaux et les dernières transactions
    """
    # Calculer les totaux pour l'utilisateur connecté
    total_recettes = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'recette'
    ).scalar() or 0

    total_depenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'depense'
    ).scalar() or 0

    benefice = total_recettes - total_depenses

    # Statistiques du mois en cours
    debut_mois = datetime.now().replace(day=1).date()
    recettes_mois = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'recette',
        Transaction.date >= debut_mois
    ).scalar() or 0

    depenses_mois = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'depense',
        Transaction.date >= debut_mois
    ).scalar() or 0

    # Nombre total de transactions
    nb_transactions = Transaction.query.filter_by(user_id=current_user.id).count()

    # Dernières transactions (5 plus récentes)
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(5).all()

    # Données pour le graphique des 7 derniers jours
    chart_data = get_chart_data(current_user.id)

    return render_template('dashboard.html',
                           total_recettes=total_recettes,
                           total_depenses=total_depenses,
                           benefice=benefice,
                           recettes_mois=recettes_mois,
                           depenses_mois=depenses_mois,
                           nb_transactions=nb_transactions,
                           recent_transactions=recent_transactions,
                           chart_data=chart_data)


@main_bp.route('/stats')
@login_required
def stats():
    """
    Page de statistiques détaillées
    Graphiques camembert, évolution mensuelle, etc.
    """
    # Période sélectionnée (par défaut: mois courant)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # Dates de la période
    start_date = datetime(year, month, 1).date()
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day).date()

    # Transactions de la période
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    # Totaux de la période
    total_recettes = sum(t.amount for t in transactions if t.type == 'recette')
    total_depenses = sum(t.amount for t in transactions if t.type == 'depense')
    benefice = total_recettes - total_depenses

    # Répartition par catégorie (pour le camembert)
    categories_recettes = {}
    categories_depenses = {}

    for t in transactions:
        if t.type == 'recette':
            categories_recettes[t.category] = categories_recettes.get(t.category, 0) + t.amount
        else:
            categories_depenses[t.category] = categories_depenses.get(t.category, 0) + t.amount

    # Données pour les graphiques
    pie_data_recettes = {
        'labels': list(categories_recettes.keys()),
        'values': list(categories_recettes.values())
    }
    pie_data_depenses = {
        'labels': list(categories_depenses.keys()),
        'values': list(categories_depenses.values())
    }

    # Évolution journalière du mois
    daily_data = get_daily_data(current_user.id, year, month)

    # Comparaison avec le mois précédent
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    prev_start = datetime(prev_year, prev_month, 1).date()
    _, prev_last_day = monthrange(prev_year, prev_month)
    prev_end = datetime(prev_year, prev_month, prev_last_day).date()

    prev_recettes = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'recette',
        Transaction.date >= prev_start,
        Transaction.date <= prev_end
    ).scalar() or 0

    prev_depenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'depense',
        Transaction.date >= prev_start,
        Transaction.date <= prev_end
    ).scalar() or 0

    # Calcul des variations
    variation_recettes = ((total_recettes - prev_recettes) / prev_recettes * 100) if prev_recettes > 0 else 0
    variation_depenses = ((total_depenses - prev_depenses) / prev_depenses * 100) if prev_depenses > 0 else 0

    # Noms des mois en français
    mois_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    return render_template('stats.html',
                           year=year,
                           month=month,
                           mois_nom=mois_fr[month],
                           total_recettes=total_recettes,
                           total_depenses=total_depenses,
                           benefice=benefice,
                           nb_transactions=len(transactions),
                           pie_data_recettes=pie_data_recettes,
                           pie_data_depenses=pie_data_depenses,
                           daily_data=daily_data,
                           prev_recettes=prev_recettes,
                           prev_depenses=prev_depenses,
                           variation_recettes=variation_recettes,
                           variation_depenses=variation_depenses,
                           mois_fr=mois_fr)


def get_chart_data(user_id):
    """
    Génère les données pour le graphique des 7 derniers jours
    """
    labels = []
    recettes = []
    depenses = []

    today = datetime.now().date()

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%d/%m'))

        # Recettes du jour
        recette_jour = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'recette',
            Transaction.date == day
        ).scalar() or 0
        recettes.append(float(recette_jour))

        # Dépenses du jour
        depense_jour = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'depense',
            Transaction.date == day
        ).scalar() or 0
        depenses.append(float(depense_jour))

    return {
        'labels': labels,
        'recettes': recettes,
        'depenses': depenses
    }


def get_daily_data(user_id, year, month):
    """
    Génère les données journalières pour un mois donné
    """
    _, last_day = monthrange(year, month)

    labels = []
    recettes = []
    depenses = []

    for day in range(1, last_day + 1):
        date_obj = datetime(year, month, day).date()
        labels.append(str(day))

        # Recettes du jour
        recette_jour = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'recette',
            Transaction.date == date_obj
        ).scalar() or 0
        recettes.append(float(recette_jour))

        # Dépenses du jour
        depense_jour = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'depense',
            Transaction.date == date_obj
        ).scalar() or 0
        depenses.append(float(depense_jour))

    return {
        'labels': labels,
        'recettes': recettes,
        'depenses': depenses
    }

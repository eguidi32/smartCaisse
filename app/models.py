"""
Modèles de base de données pour SmartCaisse
- User : utilisateurs de l'application
- Transaction : recettes et dépenses
- Client : clients avec dettes
- Dette : dettes des clients
- Paiement : paiements sur les dettes
"""
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db


class User(UserMixin, db.Model):
    """
    Modèle utilisateur pour l'authentification

    Attributs:
        id: Identifiant unique
        username: Nom d'utilisateur (unique)
        email: Email (unique)
        password_hash: Mot de passe hashé (jamais en clair!)
        role: 'admin' ou 'user'
        is_active: Compte actif ou non
        must_change_password: Doit changer le mot de passe à la prochaine connexion
        created_at: Date de création du compte
        last_login: Dernière connexion
        transactions: Relation vers les transactions de l'utilisateur
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), default='user')  # 'admin' ou 'user'
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relation one-to-many avec Transaction
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic',
                                   cascade='all, delete-orphan')

    # Relation one-to-many avec Client
    clients = db.relationship('Client', backref='user', lazy='dynamic',
                              cascade='all, delete-orphan')

    # Relation one-to-many avec Product
    products = db.relationship('Product', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash et stocke le mot de passe de manière sécurisée"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie si le mot de passe fourni correspond au hash"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role == 'admin'

    def get_id(self):
        """Requis par Flask-Login"""
        return str(self.id)

    def get_reset_token(self):
        """Génère un token sécurisé pour la réinitialisation du mot de passe"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        """
        Vérifie un token de réinitialisation et retourne l'utilisateur

        Args:
            token: Le token à vérifier
            expires_sec: Durée de validité en secondes (défaut: 1 heure)

        Returns:
            User ou None si le token est invalide/expiré
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expires_sec
            )
        except (SignatureExpired, BadSignature):
            return None
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f'<User {self.username}>'


class Transaction(db.Model):
    """
    Modèle pour les transactions (recettes et dépenses)

    Attributs:
        id: Identifiant unique
        type: 'recette' ou 'depense'
        amount: Montant de la transaction (en centimes pour éviter les erreurs de float)
        description: Description de la transaction
        category: Catégorie optionnelle
        date: Date de la transaction
        created_at: Date de création de l'enregistrement
        user_id: Clé étrangère vers l'utilisateur
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'recette' ou 'depense'
    amount = db.Column(db.Float, nullable=False)  # Montant en devise locale
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='Autre')
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Transaction {self.type}: {self.amount}>'

    @property
    def formatted_amount(self):
        """Retourne le montant formaté avec le signe approprié"""
        if self.type == 'recette':
            return f'+{self.amount:.2f}'
        return f'-{self.amount:.2f}'


# ============================================
# MODÈLES POUR LA GESTION DES DETTES
# ============================================

class Client(db.Model):
    """
    Modèle pour les clients avec dettes

    Attributs:
        id: Identifiant unique
        nom: Nom du client
        telephone: Numéro de téléphone (unique par utilisateur)
        adresse: Adresse du client
        created_at: Date de création
        user_id: Propriétaire du client (l'utilisateur connecté)
        dettes: Relation vers les dettes du client
    """
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    adresse = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Champs pour notifications email
    email = db.Column(db.String(120), nullable=True)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    email_confirmation_token = db.Column(db.String(256), nullable=True)

    # Relation one-to-many avec Dette
    dettes = db.relationship('Dette', backref='client', lazy='dynamic',
                             cascade='all, delete-orphan')

    # Contrainte unique: telephone unique par utilisateur
    __table_args__ = (
        db.UniqueConstraint('telephone', 'user_id', name='unique_phone_per_user'),
        db.UniqueConstraint('email', 'user_id', name='unique_email_per_user'),
    )

    @property
    def total_dette(self):
        """Calcule le total des dettes du client"""
        return sum(d.montant_dette for d in self.dettes)

    @property
    def total_paye(self):
        """Calcule le total payé par le client"""
        return sum(d.montant_paye for d in self.dettes)

    @property
    def total_restant(self):
        """Calcule le montant total restant à payer"""
        return sum(d.montant_restant for d in self.dettes)

    @property
    def nb_dettes_actives(self):
        """Nombre de dettes non soldées"""
        return sum(1 for d in self.dettes if d.montant_restant > 0)

    def get_email_confirmation_token(self):
        """Génère un token sécurisé pour confirmation d'email du client"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt=f'email-confirmation-salt-{self.id}')

    def set_email_confirmed(self):
        """Marque l'email comme confirmé"""
        self.email_confirmed = True
        self.email_confirmed_at = datetime.utcnow()
        self.email_confirmation_token = None

    @staticmethod
    def verify_email_confirmation_token(token, client_id, expires_sec=3600):
        """
        Vérifie un token de confirmation d'email et retourne le client

        Args:
            token: Le token à vérifier
            client_id: L'ID du client pour vérifier le salt
            expires_sec: Durée de validité en secondes (défaut: 1 heure)

        Returns:
            Client ou None si le token est invalide/expiré
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt=f'email-confirmation-salt-{client_id}',
                max_age=expires_sec
            )
        except (SignatureExpired, BadSignature):
            return None
        return Client.query.filter_by(id=client_id, email=email).first()

    def __repr__(self):
        return f'<Client {self.nom}>'


class Dette(db.Model):
    """
    Modèle pour les dettes

    Attributs:
        id: Identifiant unique
        description: Description de la dette
        montant_dette: Montant total de la dette
        date: Date de création de la dette
        client_id: Client concerné
        paiements: Relation vers les paiements
    """
    __tablename__ = 'dettes'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    montant_dette = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers Client
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Relation one-to-many avec Paiement
    paiements = db.relationship('Paiement', backref='dette', lazy='dynamic',
                                cascade='all, delete-orphan')

    @property
    def montant_paye(self):
        """Calcule le montant total payé sur cette dette"""
        return sum(p.montant for p in self.paiements)

    @property
    def montant_restant(self):
        """Calcule le montant restant à payer"""
        return self.montant_dette - self.montant_paye

    @property
    def est_soldee(self):
        """Vérifie si la dette est entièrement payée"""
        return self.montant_restant <= 0

    @property
    def pourcentage_paye(self):
        """Calcule le pourcentage payé"""
        if self.montant_dette == 0:
            return 100
        return (self.montant_paye / self.montant_dette) * 100

    def __repr__(self):
        return f'<Dette {self.id}: {self.montant_dette} FCFA>'


class Paiement(db.Model):
    """
    Modèle pour les paiements sur les dettes

    Attributs:
        id: Identifiant unique
        montant: Montant du paiement
        date: Date du paiement
        dette_id: Dette concernée
    """
    __tablename__ = 'paiements'

    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers Dette
    dette_id = db.Column(db.Integer, db.ForeignKey('dettes.id'), nullable=False)

    def __repr__(self):
        return f'<Paiement {self.montant} FCFA>'


# ============================================
# MODÈLES POUR LA GESTION DE STOCK
# ============================================

class Product(db.Model):
    """
    Modèle pour les produits en stock

    Attributs:
        id: Identifiant unique
        name: Nom du produit
        description: Description optionnelle
        price: Prix du produit (en devise locale)
        stock: Quantité actuelle en stock (calculée dynamiquement)
        created_at: Date de création
        updated_at: Date de dernière modification
        user_id: Propriétaire du produit (l'utilisateur connecté)
        movements: Relation vers les mouvements de stock
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), default='')
    price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Clé étrangère vers User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relation one-to-many avec StockMovement
    movements = db.relationship('StockMovement', backref='product', lazy='dynamic',
                                cascade='all, delete-orphan')

    # Contrainte unique: nom unique par utilisateur
    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_product_name_per_user'),
    )

    @property
    def current_stock(self):
        """Calcule le stock actual basé sur les mouvements"""
        entries = db.session.query(db.func.sum(StockMovement.quantity)).filter_by(
            product_id=self.id, type='entrée'
        ).scalar() or 0
        exits = db.session.query(db.func.sum(StockMovement.quantity)).filter_by(
            product_id=self.id, type='sortie'
        ).scalar() or 0
        return entries - exits

    @property
    def is_low_stock(self, threshold=5):
        """Vérifie si le stock est faible (seuil par défaut: 5 unités)"""
        return self.current_stock <= threshold

    def __repr__(self):
        return f'<Product {self.name}>'


class StockMovement(db.Model):
    """
    Modèle pour les mouvements de stock

    Attributs:
        id: Identifiant unique
        type: 'entrée' ou 'sortie'
        quantity: Quantité (doit être positive)
        date: Date du mouvement
        notes: Notes optionnelles
        created_at: Date d'enregistrement
        product_id: Produit concerné
    """
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'entrée' ou 'sortie'
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers Product
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def __repr__(self):
        return f'<StockMovement {self.type}: +{self.quantity if self.type == "entrée" else "-" + str(self.quantity)}>'

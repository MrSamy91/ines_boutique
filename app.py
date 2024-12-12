from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète'  # Nécessaire pour les sessions et flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boutique.db'
app.config['UPLOAD_FOLDER'] = 'static/images'
db = SQLAlchemy(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    marque = db.Column(db.String(100), nullable=False)

# Création des tables
with app.app_context():
    db.create_all()
    # Créer un admin par défaut si aucun n'existe
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

# Décorateurs
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Accès non autorisé')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor pour rendre l'utilisateur disponible dans tous les templates
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}

# Routes
@app.route('/')
def index():
    articles = Article.query.all()
    marques = db.session.query(Article.marque).distinct().all()
    return render_template('index.html', articles=articles, marques=marques)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            flash('Connexion réussie')
            return redirect(url_for('index'))
        flash('Identifiants invalides')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Ce nom d\'utilisateur est déjà pris')
            return redirect(url_for('register'))
        
        user = User(username=request.form['username'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Inscription réussie')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Déconnexion réussie')
    return redirect(url_for('index'))

@app.route('/gestion_articles')
@login_required
def gestion_articles():
    articles = Article.query.all()
    return render_template('gestion_articles.html', articles=articles)

@app.route('/ajouter_article', methods=['GET', 'POST'])
@login_required
def ajouter_article():
    if request.method == 'POST':
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        article = Article(
            nom=request.form['nom'],
            description=request.form['description'],
            prix=float(request.form['prix']),
            image=f"images/{filename}",
            marque=request.form['marque']
        )
        db.session.add(article)
        db.session.commit()
        flash('Article ajouté avec succès')
        return redirect(url_for('gestion_articles'))
    return render_template('ajouter_article.html')

@app.route('/supprimer_article/<int:id>')
@login_required
def supprimer_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash('Article supprimé avec succès')
    return redirect(url_for('gestion_articles'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True) 
'''
Arquivo principal da aplicação Flask. 
Inicializa a aplicação, registra os blueprints e define a rota principal.
'''
import os
import logging
from flask import Flask, render_template

# Importar Blueprints e funções de inicialização
import db
from routes.auth import auth_bp
from routes.feed import feed_bp
from routes.games import games_bp
from routes.ia import ia_bp

# Criação da aplicação Flask
app = Flask(__name__)

# Configuração da aplicação
BASE_DIR = os.path.dirname(__file__)
UPLOAD_ROOT = os.path.join(BASE_DIR, 'static', 'uploads')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['UPLOAD_FOLDER'] = UPLOAD_ROOT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Configuração de logging
app.logger.setLevel(logging.INFO)
if not app.logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(games_bp)
app.register_blueprint(ia_bp)

# Rota principal
@app.route('/')
def home():
    '''Página inicial da aplicação.'''
    user = db.current_user()
    return render_template('home.html', user=user)

# Ponto de entrada da aplicação
if __name__ == '__main__':
    # Garante que o DB seja inicializado antes de rodar a aplicação
    with app.app_context():
        db.init_db()
    
    # Usa a porta do ambiente (Render) ou 5002 como fallback
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

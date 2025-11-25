import os
import sqlite3
import logging
from datetime import datetime
from functools import wraps
from flask import session, flash, redirect, url_for, current_app

# Configuração de Caminhos
BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, 'db')
DB_PATH = os.path.join(DB_DIR, 'database.db')

# Configuração de Logging
logger = logging.getLogger(__name__)

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _upgrade_user_columns(conn):
    """Garante que novas colunas opcionais existam na tabela users."""
    existing_cols = {row[1] for row in conn.execute('PRAGMA table_info(users)').fetchall()}
    upgrades = []
    if 'city' not in existing_cols:
        upgrades.append('ADD COLUMN city TEXT')
    if 'status_msg' not in existing_cols:
        upgrades.append('ADD COLUMN status_msg TEXT')
    if upgrades:
        for stmt in upgrades:
            conn.execute(f'ALTER TABLE users {stmt}')
        conn.commit()

def init_db():
    """Inicializa o banco de dados SQLite com as tabelas necessárias."""
    conn = get_db_connection()
    c = conn.cursor()
    # Users table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            bio TEXT,
            city TEXT,
            status_msg TEXT,
            age INTEGER,
            gender TEXT,
            avatar_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    # Posts table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT,
            media_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    # Game scores table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    # Comments table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    # AI chat logs (optional)
    c.execute(
        '''CREATE TABLE IF NOT EXISTS ai_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    conn.commit()
    _upgrade_user_columns(conn)
    conn.close()
    logger.info("Database initialized/checked at %s", DB_PATH)

def user_best_scores(user_id):
    """Retorna a melhor pontuação por jogo para um usuário."""
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT game, MAX(score) AS best_score, MAX(created_at) AS last_played '
        'FROM scores WHERE user_id = ? GROUP BY game',
        (user_id,)
    ).fetchall()
    conn.close()
    scores = []
    for row in rows:
        scores.append({
            'game': row['game'],
            'score': row['best_score'],
            'last_played_human': datetime.fromisoformat(row['last_played']).strftime('%d/%m/%Y %H:%M')
        })
    return scores

# Funções auxiliares que serão usadas pelas rotas
def current_user():
    """Retorna o objeto do usuário logado ou None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def login_required(view_func):
    """Decorator para proteger rotas que exigem login."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash('Faça login para continuar.', 'error')
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

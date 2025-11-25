'''
Blueprint para rotas de autenticação e perfil de usuário.
'''
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import db
from db import get_db_connection, current_user, login_required, user_best_scores, allowed_file

auth_bp = Blueprint('auth', __name__)

def login_user(user):
    session['user_id'] = user['id']

def logout_user():
    session.pop('user_id', None)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        if password != password_confirm:
            flash('As senhas não conferem', 'error')
        else:
            conn = get_db_connection()
            existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
            if existing:
                flash('Usuário ou email já cadastrados', 'error')
            else:
                password_hash = generate_password_hash(password)
                conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                             (username, email, password_hash))
                conn.commit()
                current_app.logger.info("New user registered: username=%s email=%s", username, email)
                flash('Conta criada com sucesso! Faça login.', 'success')
                conn.close()
                return redirect(url_for('auth.login'))
            conn.close()
    return render_template('register.html', user=current_user())


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            login_user(user)
            current_app.logger.info("Login success user_id=%s", user['id'])
            flash('Bem-vindo de volta!', 'success')
            return redirect(url_for('home'))
        else:
            current_app.logger.warning("Login failed for identifier=%s", identifier)
            flash('Usuário ou senha incorretos', 'error')
    return render_template('login.html', user=current_user())


@auth_bp.route('/logout')
def logout():
    current_app.logger.info("Logout user_id=%s", session.get('user_id'))
    logout_user()
    flash('Sessão encerrada.', 'success')
    return redirect(url_for('home'))


@auth_bp.route('/profile')
@login_required
def profile():
    user = current_user()
    best_scores = user_best_scores(user['id'])
    return render_template('profile.html', user=user, is_self=True, best_scores=best_scores)


@auth_bp.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    viewer = current_user()
    conn = get_db_connection()
    target = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not target:
        abort(404)
    best_scores = user_best_scores(target['id'])
    return render_template('profile.html', user=target, is_self=(viewer and viewer['id'] == target['id']), best_scores=best_scores)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user()
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        bio = request.form.get('bio', '').strip()
        city = request.form.get('city', '').strip()
        status_msg = request.form.get('status_msg', '').strip()
        age = request.form.get('age', '')
        gender = request.form.get('gender', '').strip()
        avatar_file = request.files.get('avatar')
        avatar_path = user['avatar_path']
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(f"avatar_{user['id']}_{int(datetime.now().timestamp())}_{avatar_file.filename}")
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(save_path, exist_ok=True)
            full_path = os.path.join(save_path, filename)
            avatar_file.save(full_path)
            avatar_path = os.path.join('uploads', 'avatars', filename)
        # Update DB
        conn = get_db_connection()
        conn.execute('UPDATE users SET display_name=?, bio=?, city=?, status_msg=?, age=?, gender=?, avatar_path=? WHERE id=?',
                     (display_name or None, bio or None, city or None, status_msg or None, age or None, gender or None, avatar_path, user['id']))
        conn.commit()
        conn.close()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('edit_profile.html', user=user)

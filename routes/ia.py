'''
Blueprint para a rota de chat com IA.
'''
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app
import requests

import db
from db import get_db_connection, current_user, login_required

ia_bp = Blueprint('ia', __name__)

@ia_bp.route('/ia', methods=['GET', 'POST'])
@login_required
def ia_chat():
    user = current_user()
    conn = get_db_connection()
    
    # Fetch chat history
    history = conn.execute('SELECT * FROM ai_chats WHERE user_id = ? ORDER BY created_at ASC',
                          (user['id'],)).fetchall()
    messages = []
    for msg in history:
        messages.append({
            'role': msg['role'],
            'content': msg['content'],
            'created_at_human': datetime.fromisoformat(msg['created_at']).strftime('%d/%m/%Y %H:%M')
        })
        
    if request.method == 'POST':
        message = request.form['message'].strip()
        if message:
            # save user message to DB
            conn.execute('INSERT INTO ai_chats (user_id, role, content) VALUES (?, ?, ?)',
                         (user['id'], 'user', message))
            conn.commit()
            
            # send to LM Studio (assume it's running on localhost:1234)
            try:
                response = requests.post('http://127.0.0.1:1234', json={'prompt': message, 'max_tokens': 100})
                if response.ok:
                    # Assumindo que a resposta do LM Studio tem um campo 'response'
                    ai_reply = response.json().get('response', 'Resposta da IA vazia.')
                else:
                    ai_reply = 'Desculpe, a IA não respondeu como esperado (Status: {}).'.format(response.status_code)
                current_app.logger.info("IA request ok user_id=%s", user['id'])
            except requests.exceptions.ConnectionError:
                ai_reply = 'Erro ao conectar à IA local. Verifique se o LM Studio está rodando em http://127.0.0.1:1234.'
                current_app.logger.exception("IA request failed user_id=%s (Connection Error)", user['id'])
            except Exception:
                ai_reply = 'Erro desconhecido ao processar a resposta da IA local.'
                current_app.logger.exception("IA request failed user_id=%s (Unknown Error)", user['id'])
                
            # save AI response
            conn.execute('INSERT INTO ai_chats (user_id, role, content) VALUES (?, ?, ?)',
                         (user['id'], 'ai', ai_reply))
            conn.commit()
            return redirect(url_for('ia.ia_chat'))
            
    conn.close()
    return render_template('ia.html', user=user, history=messages)

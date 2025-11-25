'''
Blueprint para rotas de jogos e ranking.
'''
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app

import db
from db import get_db_connection, current_user, login_required

games_bp = Blueprint('games', __name__)

@games_bp.route('/jogos')
@login_required
def games():
    user = current_user()
    return render_template('games.html', user=user)


@games_bp.route('/jogos/tetris')
@login_required
def game_tetris():
    user = current_user()
    return render_template('game_tetris.html', user=user)


@games_bp.route('/jogos/pacman')
@login_required
def game_pacman():
    user = current_user()
    return render_template('game_pacman.html', user=user)


@games_bp.route('/jogos/ranking')
@login_required
def games_ranking():
    user = current_user()
    conn = get_db_connection()
    
    # ranking for tetris
    ranking_tetris = conn.execute(
        'SELECT users.username, users.display_name, MAX(scores.score) AS best_score, MAX(scores.created_at) AS last_played\n'
        'FROM scores JOIN users ON scores.user_id = users.id\n'
        'WHERE scores.game = "tetris"\n'
        'GROUP BY scores.user_id\n'
        'ORDER BY best_score DESC LIMIT 10'
    ).fetchall()
    
    # ranking for pacman
    ranking_pacman = conn.execute(
        'SELECT users.username, users.display_name, MAX(scores.score) AS best_score, MAX(scores.created_at) AS last_played\n'
        'FROM scores JOIN users ON scores.user_id = users.id\n'
        'WHERE scores.game = "pacman"\n'
        'GROUP BY scores.user_id\n'
        'ORDER BY best_score DESC LIMIT 10'
    ).fetchall()
    conn.close()
    
    # format results
    def format_ranking(rows):
        formatted = []
        for row in rows:
            formatted.append({
                'username': row['username'],
                'display_name': row['display_name'],
                'score': row['best_score'],
                'date_human': datetime.fromisoformat(row['last_played']).strftime('%d/%m/%Y %H:%M')
            })
        return formatted
        
    return render_template('games_ranking.html', user=user,
                           ranking_tetris=format_ranking(ranking_tetris),
                           ranking_pacman=format_ranking(ranking_pacman))


@games_bp.route('/api/jogos/score', methods=['POST'])
@login_required
def api_game_score():
    user = current_user()
    data = request.get_json(force=True)
    game = data.get('game')
    score = data.get('score')
    if not game or score is None:
        return jsonify({'error': 'invalid payload'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO scores (user_id, game, score) VALUES (?, ?, ?)',
                     (user['id'], game, int(score)))
        conn.commit()
        current_app.logger.info("Score saved user_id=%s game=%s score=%s", user['id'], game, score)
        return jsonify({'status': 'ok'})
    except ValueError:
        return jsonify({'error': 'score must be an integer'}), 400
    finally:
        conn.close()


@games_bp.route('/api/jogos/score', methods=['GET'])
@login_required
def api_game_ranking():
    game = request.args.get('game')
    limit = int(request.args.get('limit', 10))
    if not game:
        return jsonify({'error': 'game required'}), 400
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT users.username, users.display_name, MAX(scores.score) AS best_score, MAX(scores.created_at) AS last_played '
        'FROM scores JOIN users ON scores.user_id = users.id '
        'WHERE scores.game = ? '
        'GROUP BY scores.user_id '
        'ORDER BY best_score DESC '
        'LIMIT ?',
        (game, limit)
    ).fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            'username': r['username'],
            'display_name': r['display_name'],
            'score': r['best_score'],
            'last_played': r['last_played']
        })
    return jsonify({'game': game, 'ranking': items})

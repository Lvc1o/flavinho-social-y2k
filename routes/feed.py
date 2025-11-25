'''
Blueprint para o feed de posts e comentários.
'''
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename

import db
from db import get_db_connection, current_user, login_required, allowed_file

feed_bp = Blueprint("feed", __name__)

@feed_bp.route("/feed", methods=["GET", "POST"])
@login_required
def feed():
    user = current_user()
    conn = get_db_connection()
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "new_post":
            content = request.form.get("content", "").strip()
            media_file = request.files.get("media")
            media_path = None
            if media_file and allowed_file(media_file.filename):
                filename = secure_filename(f'{user["id"]}_{int(datetime.now().timestamp())}_{media_file.filename}')
                save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "posts")
                os.makedirs(save_dir, exist_ok=True)
                full_path = os.path.join(save_dir, filename)
                media_file.save(full_path)
                media_path = os.path.join("uploads", "posts", filename)
            if content or media_path:
                conn.execute("INSERT INTO posts (user_id, content, media_path) VALUES (?, ?, ?)",
                             (user["id"], content, media_path))
                conn.commit()
                current_app.logger.info("Post created by user_id=%s media=%s", user["id"], bool(media_path))
                flash("Post publicado!", "success")
            else:
                flash("O post não pode estar vazio.", "error")
            return redirect(url_for('feed.feed'))

        elif form_type == "new_comment":
            comment_content = request.form.get("comment_content", "").strip()
            post_id = request.form.get("post_id")
            if comment_content and post_id:
                conn.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                             (post_id, user["id"], comment_content))
                conn.commit()
                current_app.logger.info("Comment added user_id=%s post_id=%s", user["id"], post_id)
                flash("Comentário adicionado!", "success")
            else:
                flash("Comentário inválido.", "error")
            return redirect(url_for('feed.feed'))

    # Fetch posts and their authors
    posts_rows = conn.execute(
        '''SELECT p.*, u.username, u.display_name, u.avatar_path 
           FROM posts p JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC'''
    ).fetchall()

    # Fetch all comments and their authors
    comments_rows = conn.execute(
        '''SELECT c.*, u.username, u.display_name, u.avatar_path
           FROM comments c JOIN users u ON c.user_id = u.id
           ORDER BY c.created_at ASC'''
    ).fetchall()
    conn.close()

    # Group comments by post_id for efficient lookup
    comments_by_post = {}
    for c in comments_rows:
        if c['post_id'] not in comments_by_post:
            comments_by_post[c['post_id']] = []
        comments_by_post[c['post_id']].append({
            'id': c['id'],
            'content': c['content'],
            'created_at_human': datetime.fromisoformat(c['created_at']).strftime('%d/%m/%Y %H:%M'),
            'author': {
                'id': c['user_id'],
                'username': c['username'],
                'display_name': c['display_name'],
                'avatar_url': url_for("static", filename=c['avatar_path']) if c['avatar_path'] else url_for('static', filename='img/default-avatar.png')
            }
        })

    # Format posts for rendering
    formatted_posts = []
    for p in posts_rows:
        formatted_posts.append({
            'id': p['id'],
            'content': p['content'],
            'media_url': url_for("static", filename=p['media_path']) if p['media_path'] else None,
            'is_image': p['media_path'] and p['media_path'].split(".")[-1].lower() in {'png', 'jpg', 'jpeg', 'gif'},
            'is_video': p['media_path'] and p['media_path'].split(".")[-1].lower() in {'mp4', 'mov', 'webm'},
            'author': {
                'id': p['user_id'],
                'username': p['username'],
                'display_name': p['display_name'],
                'avatar_url': url_for("static", filename=p['avatar_path']) if p['avatar_path'] else url_for('static', filename='img/default-avatar.png')
            },
            'created_at_human': datetime.fromisoformat(p['created_at']).strftime('%d/%m/%Y %H:%M'),
            'comments': comments_by_post.get(p['id'], [])
        })

    return render_template("feed.html", user=user, posts=formatted_posts)

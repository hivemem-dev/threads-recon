#!/usr/bin/env python3
"""Веб-интерфейс поверх recon.py: добавляешь конкурентов, видишь карточки с
подписчиками/постами/топ-5 по лайкам, всё сохраняется в recon.db рядом.

Запуск:
    pip install flask
    python3 webapp.py
Дальше открой http://127.0.0.1:5050
"""
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

import recon
import storage

MAX_COMPETITORS = 5

app = Flask(__name__)


def get_db():
    conn = storage.get_db()
    storage.ensure_schema(conn)
    return conn


@app.route("/")
def index():
    conn = get_db()
    competitors = []
    for row in storage.list_competitors(conn):
        competitors.append({
            "row": row,
            "followers": storage.latest_followers(conn, row["id"]),
            "posts": storage.competitor_posts(conn, row["id"]),
            "snapshots": storage.snapshot_count(conn, row["id"]),
        })
    return render_template(
        "index.html", competitors=competitors, max_competitors=MAX_COMPETITORS,
    )


@app.route("/add", methods=["POST"])
def add():
    username = request.form.get("username", "").strip().lstrip("@")
    niche = request.form.get("niche", "").strip()
    if not username:
        return redirect(url_for("index"))
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) c FROM competitors").fetchone()["c"]
    if count >= MAX_COMPETITORS:
        return f"Уже отслеживается максимум ({MAX_COMPETITORS}) - удали кого-то, чтобы добавить нового", 400
    try:
        storage.add_competitor(conn, username, niche)
    except Exception:
        return "Этот аккаунт уже отслеживается", 400
    row = conn.execute("SELECT id FROM competitors WHERE username=?", (username,)).fetchone()
    _refresh(conn, row["id"], username)
    return redirect(url_for("index"))


@app.route("/<int:competitor_id>/refresh", methods=["POST"])
def refresh(competitor_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM competitors WHERE id=?", (competitor_id,)).fetchone()
    if not row:
        return "Не найдено", 404
    _refresh(conn, competitor_id, row["username"])
    return redirect(url_for("index"))


@app.route("/<int:competitor_id>/delete", methods=["POST"])
def delete(competitor_id):
    conn = get_db()
    storage.delete_competitor(conn, competitor_id)
    return redirect(url_for("index"))


def _refresh(conn, competitor_id, username):
    followers = None
    try:
        followers = recon.fetch_follower_count(username)
    except Exception as e:
        print(f"не удалось снять подписчиков {username}: {e}")
    posts = []
    try:
        posts = recon.fetch_posts(username)
        for p in posts:
            try:
                p["views"] = recon.fetch_post_view_count(p.get("permalink"))
            except Exception:
                p["views"] = None
            # timestamp приходит как epoch-миллисекунды (число) - переводим в
            # ISO-строку, иначе SQLite/TEXT-колонка хранит его как цифры и
            # дата в таблице показывает бессмысленный обрезок числа
            ts = p.get("timestamp")
            p["timestamp"] = datetime.fromtimestamp(ts / 1000).isoformat() if ts else None
    except Exception as e:
        print(f"не удалось снять посты {username}: {e}")
    storage.save_snapshot(conn, competitor_id, followers, posts)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)

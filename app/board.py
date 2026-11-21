from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import Post, db

bp = Blueprint("board", __name__)

KINDS = ("message", "news", "alert")


@bp.route("/")
def index():
    # alerts pinned first in every tier, then newest first
    posts = db.session.scalars(
        db.select(Post).order_by(
            (Post.kind == "alert").desc(), Post.created.desc(), Post.id.desc()
        )
    ).all()
    return render_template("board/index.html", posts=posts, kinds=KINDS)


@bp.post("/post")
def create():
    body = request.form.get("body", "").strip()
    kind = request.form.get("kind", "message")
    author = request.form.get("author", "").strip() or None

    if not body or kind not in KINDS:
        flash("A post needs some text.")
    else:
        db.session.add(Post(kind=kind, author=author, body=body))
        db.session.commit()

    return redirect(url_for("board.index"))

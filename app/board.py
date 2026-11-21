import os
import uuid
from datetime import date, timezone

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request,
    send_from_directory, url_for,
)

from .db import Attachment, Post, db, expires_on

bp = Blueprint("board", __name__)

KINDS = ("message", "news", "alert")
MAX_FILES = 4  # per post
MAX_DAYS = 30  # longest a post can stay up
# allowed extension -> attachment kind. No SVG: it can carry scripts.
MEDIA_TYPES = {
    "jpg": "image", "jpeg": "image", "png": "image", "webp": "image", "gif": "image",
    "mp4": "video", "webm": "video",
}


@bp.route("/")
def index():
    # alerts pinned first in every tier, then newest first. Expired posts are
    # skipped even if the nightly purge-expired hasn't run yet.
    posts = db.session.scalars(
        db.select(Post).where(Post.expires_on >= date.today()).order_by(
            (Post.kind == "alert").desc(), Post.created.desc(), Post.id.desc()
        )
    ).all()
    return render_template(
        "board/index.html", posts=posts, kinds=KINDS, max_days=MAX_DAYS,
        today=date.today(),
    )


def short_date(day):
    """e.g. "Fri 27 Nov", with the year only when it isn't this year."""
    text = f"{day:%a} {day.day} {day:%b}"
    return text if day.year == date.today().year else f"{text} {day.year}"


@bp.app_template_filter()
def posted(created):
    """Post time in local time: "Today, 15:41", "Yesterday, 09:12", "Thu 19 Nov, 18:05"."""
    when = created.replace(tzinfo=timezone.utc).astimezone()  # SQLite now() is UTC
    days_ago = (date.today() - when.date()).days
    if days_ago == 0:
        day = "Today"
    elif days_ago == 1:
        day = "Yesterday"
    else:
        day = short_date(when.date())
    return f"{day}, {when:%H:%M}"


@bp.app_template_filter()
def ends(last_day):
    """When the post goes: "Ends tonight", "Ends Friday night", "Ends Fri 4 Dec"."""
    days_left = (last_day - date.today()).days
    if days_left <= 0:
        return "Ends tonight"
    if days_left == 1:
        return "Ends tomorrow night"
    if days_left < 7:
        return f"Ends {last_day:%A} night"
    return f"Ends {short_date(last_day)}"


def media_kind(file):
    """Return "image" or "video" if the upload is allowed, else None."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    kind = MEDIA_TYPES.get(ext)
    # the browser's mimetype must agree with the extension
    if kind and file.mimetype.startswith(kind + "/"):
        return kind
    return None


@bp.post("/post")
def create():
    body = request.form.get("body", "").strip()
    kind = request.form.get("kind", "message")
    author = request.form.get("author", "").strip() or None
    days = request.form.get("days", type=int)
    # an empty file input still sends one part with no filename
    files = [f for f in request.files.getlist("media") if f.filename]

    if not body or kind not in KINDS:
        flash("A post needs some text.")
    elif days is None or not 1 <= days <= MAX_DAYS:
        flash(f"Say how many days the post stays up (1 to {MAX_DAYS}).")
    elif len(files) > MAX_FILES:
        flash(f"A post can have at most {MAX_FILES} photos or videos.")
    elif not all(media_kind(f) for f in files):
        flash("Only photos (JPG, PNG, WebP, GIF) and videos (MP4, WebM) can be added.")
    else:
        post = Post(kind=kind, author=author, body=body, expires_on=expires_on(days))
        for f in files:
            ext = f.filename.rsplit(".", 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            f.save(path)
            post.attachments.append(Attachment(
                filename=filename,
                original_name=f.filename[:255],
                kind=media_kind(f),
                mimetype=f.mimetype,
                size=os.path.getsize(path),
            ))
        db.session.add(post)
        db.session.commit()

    return redirect(url_for("board.index"))


@bp.post("/post/<int:post_id>/heart")
def heart(post_id):
    # increment in SQL so two clicks at the same moment both count
    result = db.session.execute(
        db.update(Post)
        .where(Post.id == post_id, Post.expires_on >= date.today())
        .values(hearts=Post.hearts + 1)
    )
    db.session.commit()
    if result.rowcount == 0:
        abort(404)  # no such post, or it has expired
    # back to the same post instead of the top of the feed
    return redirect(url_for("board.index", _anchor=f"post-{post_id}"))


@bp.errorhandler(413)
def too_large(error):
    limit = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    flash(f"Upload too large: photos and videos together can be at most {limit} MB.")
    return redirect(url_for("board.index"))


@bp.route("/media/<filename>")
def media(filename):
    # send_from_directory refuses paths outside the folder and supports
    # range requests, so videos can seek
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

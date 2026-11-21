import os
import shutil
from datetime import date, timedelta

import click
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(
        db.String(10), nullable=False, default="message"
    )  # message | news | alert
    author = db.Column(db.String(60))  # optional
    body = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, nullable=False, server_default=func.now())
    # last day the post is shown; purge-expired deletes it at the midnight after
    expires_on = db.Column(db.Date, nullable=False)
    hearts = db.Column(db.Integer, nullable=False, default=0)  # 💚 count, no per-person limit
    attachments = db.relationship(
        "Attachment", backref="post", order_by="Attachment.id",
        cascade="all, delete-orphan",
    )


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.ForeignKey("post.id"), nullable=False)
    filename = db.Column(db.String(64), nullable=False)  # name on disk: uuid4 hex + extension
    original_name = db.Column(db.String(255))  # what the user uploaded, display only
    kind = db.Column(db.String(10), nullable=False)  # image | video
    mimetype = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # bytes


def expires_on(days):
    """Last day for a post that stays up `days` days, today counting as day 1."""
    return date.today() + timedelta(days=days - 1)


def delete_expired():
    """Delete posts whose last day is over (every kind), with their uploaded files."""
    expired = db.session.scalars(
        db.select(Post).where(Post.expires_on < date.today())
    ).all()
    filenames = [a.filename for post in expired for a in post.attachments]
    for post in expired:
        db.session.delete(post)  # cascade removes the attachment rows
    db.session.commit()
    uploads = current_app.config["UPLOAD_FOLDER"]
    for filename in filenames:
        try:
            os.remove(os.path.join(uploads, filename))
        except FileNotFoundError:
            pass
    return len(expired)


@click.command("purge-expired")
def purge_expired_command():
    """Delete expired posts. Run nightly at 00:00 (cron)."""
    click.echo(f"Deleted {delete_expired()} expired post(s).")


@click.command("init-db")
def init_db_command():
    """Recreate the tables, empty the uploads folder and insert a few seed posts."""
    db.drop_all()
    uploads = current_app.config["UPLOAD_FOLDER"]
    shutil.rmtree(uploads, ignore_errors=True)
    os.makedirs(uploads)
    db.create_all()
    seeds = [
        Post(
            kind="alert",
            author="Grid ops",
            body="Storm front expected tonight. Expect reduced service.",
            expires_on=expires_on(1),
        ),
        Post(
            kind="news",
            author="Council",
            body="The community garden opens its new solar dryer on Saturday.",
        ),
        Post(
            kind="message",
            author="Mira",
            body="Anyone have spare bike tubes? Swap for tomatoes.",
        ),
        Post(kind="message", body="Lost: green thermos near the market."),
        # former hard-coded examples from board/index.html (text only, no media field yet)
        Post(
            kind="message",
            author="Sam",
            body="Our rooftop garden is finally in bloom 🌱 The tomatoes are ripe "
            "and the bees have moved in 🐝 Come and see it this weekend!",
        ),
        Post(
            kind="message",
            author="Mika",
            body="Photos from yesterday’s community bike repair 🚲🛠️ "
            "Thank you to everyone who brought tools and cake 🍰",
        ),
        Post(
            kind="message",
            author="Jules",
            body="Thank you all for helping with the market stall yesterday 🙌🍅💚 "
            "See you next Saturday!",
        ),
        Post(
            kind="news",
            author="Robin",
            body="Workshop recording: how to build a small solar charger ☀️🔧 "
            "Missed Saturday’s session? The full video is here.",
        ),
    ]
    for post in seeds:  # seeds without an explicit lifetime stay up a week
        post.expires_on = post.expires_on or expires_on(7)
    db.session.add_all(seeds)
    db.session.commit()
    click.echo("Initialized the database.")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
    app.cli.add_command(purge_expired_command)

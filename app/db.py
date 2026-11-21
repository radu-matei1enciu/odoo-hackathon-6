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
    expires_on = db.Column(db.Date, nullable=False, default=1)
    hearts = db.Column(
        db.Integer, nullable=False, default=0
    )  # green heart count, no per-person limit
    attachments = db.relationship(
        "Attachment",
        backref="post",
        order_by="Attachment.id",
        cascade="all, delete-orphan",
    )


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.ForeignKey("post.id"), nullable=False)
    filename = db.Column(
        db.String(64), nullable=False
    )  # name on disk: uuid4 hex + extension
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
            body="Storm coming in tonight, gusts up to 25 m/s after 9 pm. Tie down "
            "anything loose on the roofs. The board might go quiet for a bit if "
            "the battery runs low.",
            expires_on=expires_on(1),
        ),
        Post(
            kind="news",
            author="Council",
            body="The solar dryer at the community garden is finished. First drying "
            "day is Saturday from 10. Bring your own trays, we only have six.",
        ),
        Post(
            kind="message",
            author="Mira",
            body="Does anyone have a spare 28 inch bike tube? Can pay in tomatoes.",
        ),
        Post(
            kind="message",
            body="Lost a green thermos near the market on Thursday, dent on the lid. "
            "If you find it please leave it at the bakery.",
        ),
        Post(
            kind="message",
            author="Sam",
            body="Rooftop garden on Elm Street is finally blooming. The tomatoes are "
            "ripe and we have bees now. Come up on Sunday if you want a look, door's open.",
        ),
        Post(
            kind="message",
            author="Mika",
            body="Thanks to everyone who came to the bike repair afternoon. We got 14 "
            "bikes running again and somebody brought a whole cake. Same again next month.",
        ),
        Post(
            kind="message",
            author="Jules",
            body="Thanks for the help at the market stall yesterday, the jam was gone "
            "by noon. Same time next Saturday?",
        ),
        Post(
            kind="news",
            author="Robin",
            body="Running the solar charger workshop again next Saturday for those "
            "who missed it. Tools are there, just bring an old phone cable.",
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

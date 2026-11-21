import click
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


@click.command("init-db")
def init_db_command():
    """Recreate the tables and insert a few seed posts."""
    db.drop_all()
    db.create_all()
    db.session.add_all(
        [
            Post(
                kind="alert",
                author="Grid ops",
                body="Storm front expected tonight. Expect reduced service.",
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
        ]
    )
    db.session.commit()
    click.echo("Initialized the database.")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)

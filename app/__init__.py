import os

from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        # relative sqlite paths resolve to instance/ in Flask-SQLAlchemy 3
        SQLALCHEMY_DATABASE_URI="sqlite:///solar.db",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # whole request; larger uploads get 413
    )
    # instance/config.py overrides the defaults above if present
    app.config.from_pyfile("config.py", silent=True)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)  # also creates instance/

    from . import board, db, demo, energy

    db.init_app(app)
    energy.init_app(app)
    app.register_blueprint(board.bp)
    app.register_blueprint(demo.bp)

    return app

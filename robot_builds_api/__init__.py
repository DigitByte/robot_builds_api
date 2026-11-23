from flask import Flask

from .api import api
from .cli import promote_admin
from .config import settings
from .extensions import db, migrate


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(settings())
    app.config.update(config or {})
    if not app.config["JWT_SECRET_KEY"]:
        raise ValueError("Set JWT_SECRET_KEY before starting Flask.")
    if app.config["JWT_ACCESS_LIFETIME_MINUTES"] < 1:
        raise ValueError("JWT_ACCESS_LIFETIME_MINUTES must be positive.")
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(api)
    app.cli.add_command(promote_admin)
    return app

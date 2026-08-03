from flask import Flask

from app.extensions import db, migrate, bcrypt, jwt
from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from app.auth import auth_bp
    from app.routes import workouts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(workouts_bp)

    from app import models  # noqa: F401 — registers models with Alembic

    return app
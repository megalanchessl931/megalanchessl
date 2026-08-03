from flask import Flask
from dotenv import load_dotenv
from flask import request

from .config import Config
from .extensions import db, login_manager, migrate, csrf, limiter
from .models.user import User

def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta área."

    from flask_talisman import Talisman
    Talisman(
        app,
        force_https=app.config["FORCE_HTTPS"],
        frame_options="DENY",
        x_content_type_options=True,
        referrer_policy="no-referrer-when-downgrade",
        strict_transport_security=app.config["FORCE_HTTPS"],
        content_security_policy={
            "default-src": "'self'",
            "img-src": ["'self'", "data:"],
            "style-src": ["'self'"],
            "script-src": ["'self'"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
        },
    )

    @app.after_request
    def apply_security_headers(response):
        # Legacy header retained only because it is part of the project's
        # compatibility checklist. CSP + escaping are the primary XSS controls.
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        origin = request.headers.get("Origin")
        allowed = app.config["ALLOWED_ORIGINS"]
        if origin and origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        return response

    from .routes.public import public_bp
    from .routes.orders import orders_bp
    from .routes.admin import admin_bp
    from .routes.auth import auth_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    from .utils.csv_importer import register_import_command
    register_import_command(app)

    from .utils.security import register_security_commands
    register_security_commands(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

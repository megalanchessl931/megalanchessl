import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY não configurada. Defina-a no ambiente ou no .env.")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'app.db'}"
    )
    # Alguns provedores fornecem postgres://; SQLAlchemy moderno usa postgresql://.
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    ALLOWED_ORIGINS = {
        item.strip()
        for item in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    }
    PRINT_DEVICE = os.getenv("PRINT_DEVICE", "")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

class DevelopmentConfig(Config):
    DEBUG = True
    FORCE_HTTPS = False

class ProductionConfig(Config):
    DEBUG = False
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

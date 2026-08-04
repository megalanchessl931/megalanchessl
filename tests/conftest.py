import pytest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = "test-secret-key"

    FORCE_HTTPS = False

    ALLOWED_ORIGINS = []

    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "/tmp/megalanchessl-test-session"

    RATELIMIT_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

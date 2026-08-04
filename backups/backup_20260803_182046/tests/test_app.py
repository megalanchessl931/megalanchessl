def test_app_is_created(app):
    assert app is not None
    assert app.testing is True


def test_app_has_expected_blueprints(app):
    assert "public" in app.blueprints
    assert "orders" in app.blueprints
    assert "admin" in app.blueprints
    assert "auth" in app.blueprints
    assert "api" in app.blueprints


def test_database_is_available(app):
    from app.extensions import db

    with app.app_context():
        connection = db.engine.connect()
        connection.close()

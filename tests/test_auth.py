from app.extensions import db
from app.models import User


def create_user(app, username="usuario", email="usuario@example.com",
                password="senha123", is_admin=False):
    user = User(
        username=username,
        email=email,
        is_admin=is_admin,
    )
    user.set_password(password)

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    return user


def test_login_page(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Usu" in response.data


def test_register_page(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert b"Registro" in response.data


def test_register_valid_user(client, app):
    response = client.post(
        "/register",
        data={
            "username": "novo_usuario",
            "email": "novo@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        user = User.query.filter_by(username="novo_usuario").first()

        assert user is not None
        assert user.email == "novo@example.com"
        assert user.is_admin is False
        assert user.password_hash != "senha123"
        assert user.check_password("senha123") is True


def test_register_normalizes_username_and_email(client, app):
    response = client.post(
        "/register",
        data={
            "username": "  CarlosTeste  ",
            "email": "CARLOS@EXAMPLE.COM",
            "password": "senha123",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(username="CarlosTeste").first()

        assert user is not None
        assert user.email == "carlos@example.com"


def test_register_duplicate_username(client, app):
    create_user(
        app,
        username="existente",
        email="primeiro@example.com",
    )

    response = client.post(
        "/register",
        data={
            "username": "existente",
            "email": "segundo@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 400

    with app.app_context():
        users = User.query.filter_by(username="existente").all()
        assert len(users) == 1


def test_register_duplicate_email(client, app):
    create_user(
        app,
        username="primeiro",
        email="mesmo@example.com",
    )

    response = client.post(
        "/register",
        data={
            "username": "segundo",
            "email": "MESMO@EXAMPLE.COM",
            "password": "senha123",
        },
    )

    assert response.status_code == 400

    with app.app_context():
        user = User.query.filter_by(username="segundo").first()
        assert user is None


def test_login_with_correct_password(client, app):
    create_user(
        app,
        username="loginuser",
        email="login@example.com",
        password="senha123",
    )

    response = client.post(
        "/login",
        data={
            "username": "loginuser",
            "password": "senha123",
        },
    )

    assert response.status_code == 302
    assert "/admin/" in response.headers["Location"]


def test_login_with_wrong_password(client, app):
    create_user(
        app,
        username="loginuser",
        email="login@example.com",
        password="senha123",
    )

    response = client.post(
        "/login",
        data={
            "username": "loginuser",
            "password": "senhaerrada",
        },
    )

    assert response.status_code == 200
    assert b"Usu" in response.data


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/login",
        data={
            "username": "naoexiste",
            "password": "senha123",
        },
    )

    assert response.status_code == 200
    assert b"Usu" in response.data


def test_authenticated_user_is_redirected_from_login(client, app):
    create_user(
        app,
        username="autenticado",
        email="auth@example.com",
        password="senha123",
    )

    client.post(
        "/login",
        data={
            "username": "autenticado",
            "password": "senha123",
        },
    )

    response = client.get("/login")

    assert response.status_code == 302
    assert "/admin/" in response.headers["Location"]


def test_authenticated_user_is_redirected_from_register(client, app):
    create_user(
        app,
        username="autenticado",
        email="auth2@example.com",
        password="senha123",
    )

    client.post(
        "/login",
        data={
            "username": "autenticado",
            "password": "senha123",
        },
    )

    response = client.get("/register")

    assert response.status_code == 302
    assert "/admin/" in response.headers["Location"]


def test_logout(client, app):
    create_user(
        app,
        username="logoutuser",
        email="logout@example.com",
        password="senha123",
    )

    login_response = client.post(
        "/login",
        data={
            "username": "logoutuser",
            "password": "senha123",
        },
    )

    assert login_response.status_code == 302

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    login_page = client.get("/login")

    assert login_page.status_code == 200

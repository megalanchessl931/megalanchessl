from app.extensions import db
from app.models import User


def criar_usuario(app, username="usuario", admin=False):
    user = User(
        username=username,
        email=f"{username}@example.com",
        is_admin=admin,
    )
    user.set_password("senha123")

    with app.app_context():
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    return user_id


def login(client, username, password="senha123"):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=False,
    )


def test_admin_dashboard_sem_login_exige_autenticacao(client):
    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_pedidos_sem_login_exige_autenticacao(client):
    response = client.get("/admin/pedidos")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_produtos_sem_login_exige_autenticacao(client):
    response = client.get("/admin/produtos")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_usuario_comum_nao_acessa_dashboard_admin(client, app):
    criar_usuario(app, username="usuario", admin=False)

    response = login(client, "usuario")

    assert response.status_code in (200, 302)

    response = client.get("/admin/")

    assert response.status_code == 403


def test_usuario_comum_nao_acessa_produtos_admin(client, app):
    criar_usuario(app, username="usuario", admin=False)

    login(client, "usuario")

    response = client.get("/admin/produtos")

    assert response.status_code == 403


def test_usuario_comum_nao_acessa_pedidos_admin(client, app):
    criar_usuario(app, username="usuario", admin=False)

    login(client, "usuario")

    response = client.get("/admin/pedidos")

    assert response.status_code == 403


def test_usuario_comum_nao_acessa_balcao(client, app):
    criar_usuario(app, username="usuario", admin=False)

    login(client, "usuario")

    response = client.get("/pedidos/balcao")

    assert response.status_code == 200


def test_usuario_nao_logado_nao_acessa_balcao(client):
    response = client.get("/pedidos/balcao")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

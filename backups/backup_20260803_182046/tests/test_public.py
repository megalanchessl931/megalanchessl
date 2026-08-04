from decimal import Decimal

from app.extensions import db
from app.models import Product


def test_index_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Mega" in response.data


def test_contact_page(client):
    response = client.get("/contato")

    assert response.status_code == 200


def test_menu_page(client):
    response = client.get("/menu")

    assert response.status_code == 200


def test_active_product_appears_on_menu(client, app):
    product = Product(
        name="X-Salada Teste",
        description="Produto ativo para teste",
        price=Decimal("22.90"),
        category="LANCHE",
        is_active=True,
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200
    assert b"X-Salada Teste" in response.data


def test_inactive_product_does_not_appear_on_menu(client, app):
    product = Product(
        name="Produto Inativo Teste",
        description="Não deve aparecer",
        price=Decimal("99.90"),
        category="LANCHE",
        is_active=False,
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200
    assert b"Produto Inativo Teste" not in response.data


def test_menu_orders_active_products(client, app):
    product_b = Product(
        name="Produto B",
        price=Decimal("20.00"),
        category="LANCHE",
        order=2,
    )

    product_a = Product(
        name="Produto A",
        price=Decimal("10.00"),
        category="LANCHE",
        order=1,
    )

    with app.app_context():
        db.session.add_all([product_b, product_a])
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200

    data = response.data

    assert data.index(b"Produto A") < data.index(b"Produto B")


def test_nonexistent_page_returns_404(client):
    response = client.get("/pagina-que-nao-existe")

    assert response.status_code == 404

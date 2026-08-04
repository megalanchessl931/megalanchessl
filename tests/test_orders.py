from decimal import Decimal

from app.extensions import db
from app.models import Client, Order, OrderItem, Product, User


def criar_produto(nome="X-Burger", preco="20.00", ativo=True):
    return Product(
        name=nome,
        description="Produto de teste",
        price=Decimal(preco),
        category="LANCHE",
        is_active=ativo,
    )


def criar_usuario(
    username="balcao",
    email="balcao@example.com",
    senha="senha123",
    is_admin=False,
):
    user = User(
        username=username,
        email=email,
        is_admin=is_admin,
    )
    user.set_password(senha)
    return user


def login(client, username="balcao", senha="senha123"):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": senha,
        },
        follow_redirects=False,
    )


def test_pedido_publico_get_exibe_formulario(client):
    response = client.get("/pedidos/novo")

    assert response.status_code == 200
    assert b"Nome" in response.data
    assert b"Telefone" in response.data


def test_pedido_balcao_exige_login(client):
    response = client.get("/pedidos/balcao")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_pedido_balcao_finalizar_exige_login(client):
    response = client.post(
        "/pedidos/balcao/finalizar",
        data={
            "name": "Carlos",
            "phone": "51999999999",
        },
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_pedido_publico_sem_dados_obrigatorios_retorna_formulario(client):
    response = client.post(
        "/pedidos/novo",
        data={
            "name": "",
            "phone": "",
        },
    )

    assert response.status_code == 200
    assert b"Nome" in response.data
    assert b"Telefone" in response.data


def test_pedido_publico_com_carrinho_vazio_mostra_erro(client):
    response = client.post(
        "/pedidos/novo",
        data={
            "name": "Carlos",
            "phone": "51999999999",
        },
    )

    assert response.status_code == 200
    assert b"O carrinho est" in response.data


def test_pedido_publico_cria_pedido(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    client.post(
        "/api/cart/add",
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    response = client.post(
        "/pedidos/novo",
        data={
            "name": "Carlos",
            "phone": "51999999999",
            "address": "Rua A, 100",
            "neighborhood": "Centro",
            "notes": "Sem cebola",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/menu" in response.headers["Location"]

    with app.app_context():
        order = Order.query.one()

        assert order.total == Decimal("40.00")
        assert order.delivery_fee == Decimal("0.00")
        assert order.status == "PENDENTE"
        assert order.notes == "Sem cebola"
        assert order.user_id is None

        assert order.client.name == "Carlos"
        assert order.client.phone == "51999999999"
        assert order.client.address == "Rua A, 100"
        assert order.client.neighborhood == "Centro"

        assert len(order.items) == 1
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == Decimal("20.00")
        assert order.items[0].subtotal == Decimal("40.00")


def test_pedido_publico_limpa_carrinho_apos_finalizacao(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    client.post(
        "/api/cart/add",
        json={"product_id": product_id},
    )

    response = client.post(
        "/pedidos/novo",
        data={
            "name": "Carlos",
            "phone": "51999999999",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    cart_response = client.get("/api/cart/get")

    assert cart_response.status_code == 200

    cart = cart_response.get_json()["cart"]

    assert cart["items"] == []
    assert cart["total"] == "0.00"
    assert cart["client_id"] is None


def test_pedido_balcao_cria_pedido_associado_usuario(client, app):
    user = criar_usuario()

    product = criar_produto()

    with app.app_context():
        db.session.add_all([user, product])
        db.session.commit()

        user_id = user.id
        product_id = product.id

    login_response = login(client)

    assert login_response.status_code == 302

    client.post(
        "/api/cart/add",
        json={"product_id": product_id},
    )

    response = client.post(
        "/pedidos/balcao/finalizar",
        data={
            "name": "Cliente Balcão",
            "phone": "51988888888",
            "address": "Rua do Balcão",
            "neighborhood": "Centro",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/pedidos/balcao" in response.headers["Location"]

    with app.app_context():
        order = Order.query.one()

        assert order.user_id == user_id
        assert order.client.name == "Cliente Balcão"
        assert order.total == Decimal("20.00")


def test_pedido_publico_produto_desativado_mostra_erro(client, app):
    product = criar_produto(ativo=True)

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    client.post(
        "/api/cart/add",
        json={"product_id": product_id},
    )

    with app.app_context():
        saved_product = db.session.get(Product, product_id)
        saved_product.is_active = False
        db.session.commit()

    response = client.post(
        "/pedidos/novo",
        data={
            "name": "Carlos",
            "phone": "51999999999",
        },
    )

    assert response.status_code == 200
    assert b"n" in response.data


def test_pedido_publico_atualiza_cliente_existente(client, app):
    cliente = Client(
        name="Nome Antigo",
        phone="51999999999",
        address="Endereço Antigo",
        neighborhood="Bairro Antigo",
    )

    product = criar_produto()

    with app.app_context():
        db.session.add_all([cliente, product])
        db.session.commit()

        client_id = cliente.id
        product_id = product.id

    client.post(
        "/api/cart/add",
        json={"product_id": product_id},
    )

    response = client.post(
        "/pedidos/novo",
        data={
            "name": "Nome Novo",
            "phone": "51999999999",
            "address": "Endereço Novo",
            "neighborhood": "Centro",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        saved_client = db.session.get(Client, client_id)

        assert saved_client.name == "Nome Novo"
        assert saved_client.address == "Endereço Novo"
        assert saved_client.neighborhood == "Centro"

        assert Client.query.count() == 1
        assert Order.query.count() == 1


def test_pedido_balcao_get_exibe_produtos_ativos(client, app):
    user = criar_usuario()

    produto_ativo = criar_produto(
        nome="Produto Ativo",
        ativo=True,
    )

    produto_inativo = criar_produto(
        nome="Produto Inativo",
        ativo=False,
    )

    with app.app_context():
        db.session.add_all([user, produto_ativo, produto_inativo])
        db.session.commit()

    login_response = login(client)

    assert login_response.status_code == 302

    response = client.get("/pedidos/balcao")

    assert response.status_code == 200
    assert b"Produto Ativo" in response.data
    assert b"Produto Inativo" not in response.data


def test_pedido_publico_get_exibe_produtos_ativos(client, app):
    produto_ativo = criar_produto(
        nome="Produto Ativo",
        ativo=True,
    )

    produto_inativo = criar_produto(
        nome="Produto Inativo",
        ativo=False,
    )

    with app.app_context():
        db.session.add_all([produto_ativo, produto_inativo])
        db.session.commit()

    response = client.get("/pedidos/novo")

    assert response.status_code == 200
    assert b"Produto Ativo" in response.data
    assert b"Produto Inativo" not in response.data

from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Client, Order, OrderItem, Product, User
from app.services import order_service


def criar_produto(nome="X-Burger", preco="20.00", ativo=True):
    return Product(
        name=nome,
        description="Produto de teste",
        price=Decimal(preco),
        category="LANCHE",
        is_active=ativo,
    )


def criar_carrinho(product_id, quantidade=1, nome="X-Burger", telefone="51999999999"):
    return {
        "items": [
            {
                "product_id": product_id,
                "product_name": nome,
                "quantity": quantidade,
                "unit_price": "20.00",
                "subtotal": f"{20 * quantidade:.2f}",
            }
        ],
        "total": f"{20 * quantidade:.2f}",
        "client_id": None,
        "client_data": {
            "name": "Cliente Teste",
            "phone": telefone,
            "address": "Rua de Teste, 100",
            "neighborhood": "Centro",
        },
        "delivery_fee": "0.00",
        "notes": "",
    }


def test_criar_pedido_a_partir_do_carrinho(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id, quantidade=2)

        order = order_service.create_order_from_cart(cart)

        assert order.id is not None
        assert order.total == Decimal("40.00")
        assert order.delivery_fee == Decimal("0.00")
        assert order.status == "PENDENTE"

        assert order.client is not None
        assert order.client.name == "Cliente Teste"
        assert order.client.phone == "51999999999"

        assert len(order.items) == 1
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == Decimal("20.00")
        assert order.items[0].subtotal == Decimal("40.00")


def test_criar_cliente_novo_automaticamente(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)

        order = order_service.create_order_from_cart(cart)

        client = db.session.get(Client, order.client_id)

        assert client is not None
        assert client.name == "Cliente Teste"
        assert client.phone == "51999999999"
        assert client.address == "Rua de Teste, 100"
        assert client.neighborhood == "Centro"


def test_reutilizar_cliente_existente_pelo_telefone(app):
    product = criar_produto()

    existing_client = Client(
        name="Nome Antigo",
        phone="51999999999",
        address="Endereço Antigo",
        neighborhood="Bairro Antigo",
    )

    with app.app_context():
        db.session.add_all([product, existing_client])
        db.session.commit()

        client_id = existing_client.id

        cart = criar_carrinho(product.id)

        order = order_service.create_order_from_cart(cart)

        assert order.client_id == client_id

        client = db.session.get(Client, client_id)

        assert client.name == "Cliente Teste"
        assert client.phone == "51999999999"
        assert client.address == "Rua de Teste, 100"
        assert client.neighborhood == "Centro"

        assert Client.query.count() == 1


def test_atualizar_dados_do_cliente_existente(app):
    product = criar_produto()

    existing_client = Client(
        name="Nome Antigo",
        phone="51988888888",
        address="Rua Antiga",
        neighborhood="Bairro Antigo",
    )

    with app.app_context():
        db.session.add_all([product, existing_client])
        db.session.commit()

        cart = criar_carrinho(
            product.id,
            telefone="51988888888",
        )

        order = order_service.create_order_from_cart(cart)

        client = db.session.get(Client, order.client_id)

        assert client.name == "Cliente Teste"
        assert client.address == "Rua de Teste, 100"
        assert client.neighborhood == "Centro"


def test_carrinho_vazio_nao_cria_pedido(app):
    with app.app_context():
        cart = {
            "items": [],
            "client_data": {
                "name": "Cliente Teste",
                "phone": "51999999999",
            },
        }

        with pytest.raises(ValueError, match="carrinho está vazio"):
            order_service.create_order_from_cart(cart)

        assert Order.query.count() == 0


def test_nome_do_cliente_e_obrigatorio(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)
        cart["client_data"]["name"] = ""

        with pytest.raises(ValueError, match="Nome e telefone"):
            order_service.create_order_from_cart(cart)

        assert Order.query.count() == 0


def test_telefone_do_cliente_e_obrigatorio(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)
        cart["client_data"]["phone"] = ""

        with pytest.raises(ValueError, match="Nome e telefone"):
            order_service.create_order_from_cart(cart)

        assert Order.query.count() == 0


def test_produto_desativado_impede_finalizacao(app):
    product = criar_produto(ativo=True)

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)

        product.is_active = False
        db.session.commit()

        with pytest.raises(ValueError, match="não está mais disponível"):
            order_service.create_order_from_cart(cart)

        assert Order.query.count() == 0


def test_preco_do_pedido_vem_do_banco(app):
    product = criar_produto(preco="20.00")

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)

        # O carrinho está com R$ 20,00.
        # Alteramos o preço no banco antes da finalização.
        product.price = Decimal("25.00")
        db.session.commit()

        order = order_service.create_order_from_cart(cart)

        assert order.items[0].unit_price == Decimal("25.00")
        assert order.items[0].subtotal == Decimal("25.00")
        assert order.total == Decimal("25.00")


def test_calcular_subtotal_com_quantidade(app):
    product = criar_produto(preco="15.50")

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id, quantidade=3)

        order = order_service.create_order_from_cart(cart)

        assert order.items[0].quantity == 3
        assert order.items[0].unit_price == Decimal("15.50")
        assert order.items[0].subtotal == Decimal("46.50")
        assert order.total == Decimal("46.50")


def test_calcular_taxa_de_entrega(app):
    product = criar_produto(preco="20.00")

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id, quantidade=2)
        cart["delivery_fee"] = "7.50"

        order = order_service.create_order_from_cart(cart)

        assert order.delivery_fee == Decimal("7.50")
        assert order.total == Decimal("47.50")


def test_taxa_de_entrega_fornecida_pelo_argumento_tem_precedencia(app):
    product = criar_produto(preco="20.00")

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)
        cart["delivery_fee"] = "5.00"

        order = order_service.create_order_from_cart(
            cart,
            delivery_fee=8.50,
        )

        assert order.delivery_fee == Decimal("8.50")
        assert order.total == Decimal("28.50")


def test_salvar_observacoes_do_pedido(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)
        cart["notes"] = "  Sem cebola e sem tomate  "

        order = order_service.create_order_from_cart(cart)

        assert order.notes == "Sem cebola e sem tomate"


def test_pedido_de_balcao_associa_usuario(app):
    product = criar_produto()

    user = User(
        username="atendente",
        email="atendente@example.com",
        is_admin=True,
    )
    user.set_password("senha12345")

    with app.app_context():
        db.session.add_all([product, user])
        db.session.commit()

        cart = criar_carrinho(product.id)

        order = order_service.create_order_from_cart(
            cart,
            user=user,
        )

        assert order.user_id == user.id
        assert order.user is not None
        assert order.user.username == "atendente"


def test_pedido_publico_nao_associa_usuario(app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        cart = criar_carrinho(product.id)

        order = order_service.create_order_from_cart(
            cart,
            user=None,
        )

        assert order.user_id is None

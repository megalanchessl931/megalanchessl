from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Product
from app.services import cart_service


def criar_produto(nome="X-Burger", preco="18.00", ativo=True):
    produto = Product(
        name=nome,
        price=Decimal(preco),
        category="Lanches",
        is_active=ativo,
    )
    db.session.add(produto)
    db.session.commit()
    return produto


def test_carrinho_inicial_vazio(app):
    with app.test_request_context():
        cart = cart_service.get_cart()

        assert cart["items"] == []
        assert cart["total"] == "0.00"
        assert cart["client_id"] is None
        assert cart["delivery_fee"] == "0.00"
        assert cart["notes"] == ""
        assert cart_service.is_empty(cart) is True


def test_adicionar_produto_ao_carrinho(app):
    with app.test_request_context():
        produto = criar_produto()

        cart = cart_service.add_item(produto.id, 1)

        assert len(cart["items"]) == 1
        assert cart["items"][0]["product_id"] == produto.id
        assert cart["items"][0]["product_name"] == "X-Burger"
        assert cart["items"][0]["quantity"] == 1
        assert cart["items"][0]["unit_price"] == "18.00"
        assert cart["items"][0]["subtotal"] == "18.00"
        assert cart["total"] == "18.00"


def test_adicionar_mesmo_produto_soma_quantidade(app):
    with app.test_request_context():
        produto = criar_produto()

        cart_service.add_item(produto.id, 2)
        cart = cart_service.add_item(produto.id, 3)

        assert len(cart["items"]) == 1
        assert cart["items"][0]["quantity"] == 5
        assert cart["items"][0]["subtotal"] == "90.00"
        assert cart["total"] == "90.00"


def test_adicionar_dois_produtos_calcula_total(app):
    with app.test_request_context():
        produto1 = criar_produto("X-Burger", "18.00")
        produto2 = criar_produto("Batata", "12.00")

        cart_service.add_item(produto1.id, 2)
        cart = cart_service.add_item(produto2.id, 1)

        assert len(cart["items"]) == 2
        assert cart["total"] == "48.00"


def test_remover_produto(app):
    with app.test_request_context():
        produto1 = criar_produto("X-Burger", "18.00")
        produto2 = criar_produto("Batata", "12.00")

        cart_service.add_item(produto1.id, 1)
        cart_service.add_item(produto2.id, 1)

        cart = cart_service.remove_item(produto1.id)

        assert len(cart["items"]) == 1
        assert cart["items"][0]["product_id"] == produto2.id
        assert cart["total"] == "12.00"


def test_atualizar_quantidade(app):
    with app.test_request_context():
        produto = criar_produto()

        cart_service.add_item(produto.id, 1)
        cart = cart_service.update_quantity(produto.id, 4)

        assert cart["items"][0]["quantity"] == 4
        assert cart["items"][0]["subtotal"] == "72.00"
        assert cart["total"] == "72.00"


def test_atualizar_quantidade_zero_remove_produto(app):
    with app.test_request_context():
        produto = criar_produto()

        cart_service.add_item(produto.id, 2)
        cart = cart_service.update_quantity(produto.id, 0)

        assert cart["items"] == []
        assert cart["total"] == "0.00"
        assert cart_service.is_empty(cart) is True


def test_limpar_carrinho(app):
    with app.test_request_context():
        produto = criar_produto()

        cart_service.add_item(produto.id, 2)
        cart_service.set_notes("Sem cebola")

        cart = cart_service.clear_cart()

        assert cart["items"] == []
        assert cart["total"] == "0.00"
        assert cart["notes"] == ""
        assert cart["client_id"] is None


def test_carrinho_com_taxa_entrega(app):
    with app.test_request_context():
        produto = criar_produto("X-Burger", "18.00")

        cart_service.add_item(produto.id, 2)

        cart = cart_service.get_cart()
        cart["delivery_fee"] = "5.00"
        cart_service._salvar(cart)

        cart = cart_service.get_cart()
        cart_service._recalcular_total(cart)

        assert cart["total"] == "41.00"


def test_produto_inativo_nao_pode_ser_adicionado(app):
    with app.test_request_context():
        produto = criar_produto(ativo=False)

        with pytest.raises(ValueError, match="Produto não encontrado ou indisponível"):
            cart_service.add_item(produto.id, 1)


def test_produto_inexistente_nao_pode_ser_adicionado(app):
    with app.test_request_context():
        with pytest.raises(ValueError, match="Produto não encontrado ou indisponível"):
            cart_service.add_item(99999, 1)


def test_quantidade_invalida(app):
    with app.test_request_context():
        produto = criar_produto()

        with pytest.raises(ValueError, match="Quantidade inválida"):
            cart_service.add_item(produto.id, "abc")


def test_quantidade_zero_na_adicao_e_invalida(app):
    with app.test_request_context():
        produto = criar_produto()

        with pytest.raises(ValueError, match="Quantidade deve ser maior que zero"):
            cart_service.add_item(produto.id, 0)


def test_set_client_data(app):
    with app.test_request_context():
        cart = cart_service.set_client_data(
            name=" João Silva ",
            phone=" 51999999999 ",
            address=" Rua A ",
            neighborhood=" Centro ",
            client_id=10,
        )

        assert cart["client_id"] == 10
        assert cart["client_data"]["name"] == "João Silva"
        assert cart["client_data"]["phone"] == "51999999999"
        assert cart["client_data"]["address"] == "Rua A"
        assert cart["client_data"]["neighborhood"] == "Centro"


def test_set_notes_remove_espacos(app):
    with app.test_request_context():
        cart = cart_service.set_notes("  Sem tomate  ")

        assert cart["notes"] == "Sem tomate"


def test_preco_do_produto_vem_do_banco(app):
    with app.test_request_context():
        produto = criar_produto("X-Burger", "18.00")

        cart = cart_service.add_item(produto.id, 1)

        assert cart["items"][0]["unit_price"] == "18.00"
        assert cart["items"][0]["subtotal"] == "18.00"


def test_item_inexistente_nao_pode_ser_atualizado(app):
    with app.test_request_context():
        with pytest.raises(ValueError, match="Item não encontrado no carrinho"):
            cart_service.update_quantity(99999, 2)

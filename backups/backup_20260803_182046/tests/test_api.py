from decimal import Decimal

from app.extensions import db
from app.models import Client, Product
from app.services import cart_service


def criar_produto(nome="X-Burger", preco="20.00", ativo=True):
    return Product(
        name=nome,
        description="Produto de teste",
        price=Decimal(preco),
        category="LANCHE",
        is_active=ativo,
    )


def csrf_headers():
    """
    Os testes usam WTF_CSRF_ENABLED=False no TestConfig.
    Mantemos uma função para deixar explícito que as requisições POST
    da API são intencionais e facilitar eventual ativação de CSRF real.
    """
    return {}


def test_cart_get_retorna_carrinho_vazio(client):
    response = client.get("/api/cart/get")

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert data["cart"]["items"] == []
    assert data["cart"]["total"] == "0.00"
    assert data["cart"]["client_id"] is None


def test_cart_add_adiciona_produto(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.post(
        "/api/cart/add",
        json={"product_id": product_id},
        headers=csrf_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert len(data["cart"]["items"]) == 1

    item = data["cart"]["items"][0]

    assert item["product_id"] == product_id
    assert item["product_name"] == "X-Burger"
    assert item["quantity"] == 1
    assert item["unit_price"] == "20.00"
    assert item["subtotal"] == "20.00"
    assert data["cart"]["total"] == "20.00"


def test_cart_add_aceita_form_data(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.post(
        "/api/cart/add",
        data={"product_id": str(product_id), "quantity": "2"},
        headers=csrf_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert data["cart"]["items"][0]["quantity"] == 2
    assert data["cart"]["total"] == "40.00"


def test_cart_add_soma_mesmo_produto(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response1 = client.post(
        "/api/cart/add",
        json={"product_id": product_id, "quantity": 2},
    )

    response2 = client.post(
        "/api/cart/add",
        json={"product_id": product_id, "quantity": 3},
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data = response2.get_json()

    assert len(data["cart"]["items"]) == 1
    assert data["cart"]["items"][0]["quantity"] == 5
    assert data["cart"]["items"][0]["subtotal"] == "100.00"
    assert data["cart"]["total"] == "100.00"


def test_cart_add_sem_product_id_retorna_400(client):
    response = client.post(
        "/api/cart/add",
        json={},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "product_id" in data["erro"]


def test_cart_add_produto_inexistente_retorna_400(client):
    response = client.post(
        "/api/cart/add",
        json={"product_id": 999999},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Produto não encontrado" in data["erro"]


def test_cart_add_produto_inativo_retorna_400(client, app):
    product = criar_produto(ativo=False)

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.post(
        "/api/cart/add",
        json={"product_id": product_id},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Produto não encontrado" in data["erro"]


def test_cart_add_quantidade_invalida_retorna_400(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.post(
        "/api/cart/add",
        json={
            "product_id": product_id,
            "quantity": "abc",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Quantidade inválida" in data["erro"]


def test_cart_remove_remove_produto(client, app):
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
        "/api/cart/remove",
        json={"product_id": product_id},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert data["cart"]["items"] == []
    assert data["cart"]["total"] == "0.00"


def test_cart_remove_sem_product_id_retorna_400(client):
    response = client.post(
        "/api/cart/remove",
        json={},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "product_id" in data["erro"]


def test_cart_update_atualiza_quantidade(client, app):
    product = criar_produto()

    with app.app_context():
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    client.post(
        "/api/cart/add",
        json={"product_id": product_id, "quantity": 2},
    )

    response = client.post(
        "/api/cart/update",
        json={
            "product_id": product_id,
            "quantity": 5,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["cart"]["items"][0]["quantity"] == 5
    assert data["cart"]["items"][0]["subtotal"] == "100.00"
    assert data["cart"]["total"] == "100.00"


def test_cart_update_quantidade_zero_remove_produto(client, app):
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
        "/api/cart/update",
        json={
            "product_id": product_id,
            "quantity": 0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["cart"]["items"] == []
    assert data["cart"]["total"] == "0.00"


def test_cart_update_item_inexistente_retorna_400(client):
    response = client.post(
        "/api/cart/update",
        json={
            "product_id": 999999,
            "quantity": 2,
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Item não encontrado" in data["erro"]


def test_cart_update_sem_dados_obrigatorios_retorna_400(client):
    response = client.post(
        "/api/cart/update",
        json={"product_id": 1},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "product_id e quantity" in data["erro"]


def test_cart_clear_esvazia_carrinho(client, app):
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
        "/api/cart/clear",
        json={},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert data["cart"]["items"] == []
    assert data["cart"]["total"] == "0.00"
    assert data["cart"]["client_id"] is None


def test_client_search_exige_minimo_tres_digitos(client):
    response = client.get(
        "/api/client/search",
        query_string={"phone": "51"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "3 dígitos" in data["erro"]


def test_client_search_normaliza_telefone(client, app):
    client1 = Client(
        name="Carlos",
        phone="51999999999",
        address="Rua A",
        neighborhood="Centro",
    )

    with app.app_context():
        db.session.add(client1)
        db.session.commit()

    response = client.get(
        "/api/client/search",
        query_string={"phone": "(51) 99999-9999"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert len(data["clientes"]) == 1
    assert data["clientes"][0]["name"] == "Carlos"
    assert data["clientes"][0]["phone"] == "51999999999"


def test_client_search_busca_parcial(client, app):
    client1 = Client(
        name="Carlos",
        phone="51999999999",
    )

    client2 = Client(
        name="Ana",
        phone="51988888888",
    )

    with app.app_context():
        db.session.add_all([client1, client2])
        db.session.commit()

    response = client.get(
        "/api/client/search",
        query_string={"phone": "999"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert len(data["clientes"]) == 1
    assert data["clientes"][0]["name"] == "Carlos"


def test_client_search_retorna_campos_do_cliente(client, app):
    cliente = Client(
        name="Cliente Completo",
        phone="51911111111",
        address="Rua Teste, 100",
        neighborhood="Centro",
    )

    with app.app_context():
        db.session.add(cliente)
        db.session.commit()
        cliente_id = cliente.id

    response = client.get(
        "/api/client/search",
        query_string={"phone": "911"},
    )

    assert response.status_code == 200

    data = response.get_json()

    encontrado = data["clientes"][0]

    assert encontrado["id"] == cliente_id
    assert encontrado["name"] == "Cliente Completo"
    assert encontrado["phone"] == "51911111111"
    assert encontrado["address"] == "Rua Teste, 100"
    assert encontrado["neighborhood"] == "Centro"


def test_client_create_cria_cliente(client, app):
    response = client.post(
        "/api/client/create",
        json={
            "name": "  Carlos Teste  ",
            "phone": " 51999999999 ",
            "address": " Rua A, 100 ",
            "neighborhood": " Centro ",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True

    assert data["client"]["name"] == "Carlos Teste"
    assert data["client"]["phone"] == "51999999999"
    assert data["client"]["address"] == "Rua A, 100"
    assert data["client"]["neighborhood"] == "Centro"

    with app.app_context():
        saved = db.session.get(Client, data["client"]["id"])

        assert saved is not None
        assert saved.name == "Carlos Teste"
        assert saved.phone == "51999999999"


def test_client_create_aceita_form_data(client, app):
    response = client.post(
        "/api/client/create",
        data={
            "name": "Ana",
            "phone": "51988888888",
            "address": "Rua B",
            "neighborhood": "Centro",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ok"] is True
    assert data["client"]["name"] == "Ana"

    with app.app_context():
        assert Client.query.count() == 1


def test_client_create_atualiza_cliente_existente(client, app):
    cliente = Client(
        name="Nome Antigo",
        phone="51999999999",
        address="Endereço Antigo",
        neighborhood="Bairro Antigo",
    )

    with app.app_context():
        db.session.add(cliente)
        db.session.commit()
        client_id = cliente.id

    response = client.post(
        "/api/client/create",
        json={
            "name": "Nome Novo",
            "phone": "51999999999",
            "address": "Endereço Novo",
            "neighborhood": "Centro",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["client"]["id"] == client_id
    assert data["client"]["name"] == "Nome Novo"
    assert data["client"]["address"] == "Endereço Novo"
    assert data["client"]["neighborhood"] == "Centro"

    with app.app_context():
        assert Client.query.count() == 1

        saved = db.session.get(Client, client_id)

        assert saved.name == "Nome Novo"
        assert saved.address == "Endereço Novo"
        assert saved.neighborhood == "Centro"


def test_client_create_sem_nome_retorna_400(client):
    response = client.post(
        "/api/client/create",
        json={
            "phone": "51999999999",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Nome e telefone" in data["erro"]


def test_client_create_sem_telefone_retorna_400(client):
    response = client.post(
        "/api/client/create",
        json={
            "name": "Carlos",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Nome e telefone" in data["erro"]


def test_client_create_coloca_cliente_no_carrinho(client, app):
    response = client.post(
        "/api/client/create",
        json={
            "name": "Carlos",
            "phone": "51999999999",
            "address": "Rua A",
            "neighborhood": "Centro",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["cart"]["client_id"] == data["client"]["id"]

    assert data["cart"]["client_data"]["name"] == "Carlos"
    assert data["cart"]["client_data"]["phone"] == "51999999999"
    assert data["cart"]["client_data"]["address"] == "Rua A"
    assert data["cart"]["client_data"]["neighborhood"] == "Centro"


def test_client_search_ordena_por_nome(client, app):
    cliente_b = Client(
        name="Zeca",
        phone="51911111111",
    )

    cliente_a = Client(
        name="Ana",
        phone="51922222222",
    )

    with app.app_context():
        db.session.add_all([cliente_b, cliente_a])
        db.session.commit()

    response = client.get(
        "/api/client/search",
        query_string={"phone": "519"},
    )

    assert response.status_code == 200

    data = response.get_json()

    nomes = [cliente["name"] for cliente in data["clientes"]]

    assert nomes == ["Ana", "Zeca"]

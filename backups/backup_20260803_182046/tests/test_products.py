from decimal import Decimal

from app.extensions import db
from app.models import Product


def criar_produto(
    nome="X-Burger",
    preco="20.00",
    categoria="LANCHE",
    ativo=True,
    ordem=0,
    descricao="Produto de teste",
    imagem="placeholder.jpg",
):
    return Product(
        name=nome,
        description=descricao,
        price=Decimal(preco),
        category=categoria,
        is_active=ativo,
        order=ordem,
        image_filename=imagem,
    )


def test_criar_produto_com_dados_completos(app):
    product = criar_produto(
        nome="X-Salada",
        preco="25.90",
        categoria="LANCHE",
        descricao="Hambúrguer com salada",
        imagem="x-salada.jpg",
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved = db.session.get(Product, product.id)

        assert saved is not None
        assert saved.name == "X-Salada"
        assert saved.description == "Hambúrguer com salada"
        assert saved.price == Decimal("25.90")
        assert saved.category == "LANCHE"
        assert saved.image_filename == "x-salada.jpg"
        assert saved.is_active is True
        assert saved.order == 0


def test_produto_recebe_placeholder_como_imagem_padrao(app):
    product = Product(
        name="Produto Sem Imagem",
        price=Decimal("10.00"),
        category="LANCHE",
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved = db.session.get(Product, product.id)

        assert saved.image_filename == "placeholder.jpg"


def test_produto_fica_ativo_por_padrao(app):
    product = Product(
        name="Produto Ativo",
        price=Decimal("15.00"),
        category="LANCHE",
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved = db.session.get(Product, product.id)

        assert saved.is_active is True


def test_produto_recebe_ordem_zero_por_padrao(app):
    product = Product(
        name="Produto Ordem",
        price=Decimal("15.00"),
        category="LANCHE",
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved = db.session.get(Product, product.id)

        assert saved.order == 0


def test_produto_inativo_pode_ser_salvo(app):
    product = criar_produto(
        nome="Produto Inativo",
        ativo=False,
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved = db.session.get(Product, product.id)

        assert saved is not None
        assert saved.is_active is False


def test_menu_exibe_somente_produtos_ativos(client, app):
    ativo = criar_produto(
        nome="Produto Ativo",
        ativo=True,
    )

    inativo = criar_produto(
        nome="Produto Inativo",
        ativo=False,
    )

    with app.app_context():
        db.session.add_all([ativo, inativo])
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "Produto Ativo" in html
    assert "Produto Inativo" not in html


def test_menu_ordena_produtos_por_ordem(client, app):
    produto_segundo = criar_produto(
        nome="Segundo",
        ordem=2,
    )

    produto_primeiro = criar_produto(
        nome="Primeiro",
        ordem=1,
    )

    with app.app_context():
        db.session.add_all([produto_segundo, produto_primeiro])
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert html.index("Primeiro") < html.index("Segundo")


def test_menu_ordena_por_categoria_depois_da_ordem(client, app):
    produto_lanche = criar_produto(
        nome="Lanche",
        categoria="LANCHE",
        ordem=1,
    )

    produto_bebida = criar_produto(
        nome="Bebida",
        categoria="BEBIDA",
        ordem=1,
    )

    with app.app_context():
        db.session.add_all([produto_lanche, produto_bebida])
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert html.index("Bebida") < html.index("Lanche")


def test_menu_ordena_por_nome_com_mesma_ordem_e_categoria(client, app):
    produto_z = criar_produto(
        nome="Z-Burger",
        categoria="LANCHE",
        ordem=1,
    )

    produto_a = criar_produto(
        nome="A-Burger",
        categoria="LANCHE",
        ordem=1,
    )

    with app.app_context():
        db.session.add_all([produto_z, produto_a])
        db.session.commit()

    response = client.get("/menu")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert html.index("A-Burger") < html.index("Z-Burger")

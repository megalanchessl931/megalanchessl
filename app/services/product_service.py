import os
import uuid
from decimal import Decimal, ROUND_HALF_UP

from werkzeug.utils import secure_filename

from ..models import Product, db


# ==========================================================
# IMPORTAÇÃO / CSV (função original mantida)
# ==========================================================

def upsert_product(*, name, description, price, image_filename, category, order=0):
    product = Product.query.filter_by(name=name).first()
    if product is None:
        product = Product(name=name)
        db.session.add(product)

    product.description = description
    product.price = Decimal(price)
    product.image_filename = image_filename or "placeholder.jpg"
    product.category = category
    product.order = order
    product.is_active = True
    return product


# ==========================================================
# UPLOAD DE IMAGEM
# ==========================================================

def salvar_imagem_produto(file_storage, upload_folder):
    """
    Salva a imagem enviada no formulário com um nome de arquivo único
    e seguro, evitando sobrescrever imagens de outros produtos com o
    mesmo nome original. Retorna apenas o nome do arquivo salvo
    (sem o caminho completo), que é o que fica gravado no banco.
    """
    nome_original = secure_filename(file_storage.filename)
    extensao = nome_original.rsplit(".", 1)[-1].lower()
    nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"

    os.makedirs(upload_folder, exist_ok=True)
    caminho_completo = os.path.join(upload_folder, nome_arquivo)
    file_storage.save(caminho_completo)

    return nome_arquivo


# ==========================================================
# CRUD DE PRODUTO (painel administrativo)
# ==========================================================

def criar_produto(*, name, description, price, category, image_filename, order, is_active):
    product = Product(
        name=name,
        description=description,
        price=price,
        category=category,
        image_filename=image_filename or "placeholder.jpg",
        order=order or 0,
        is_active=is_active,
    )
    db.session.add(product)
    db.session.commit()
    return product


def atualizar_produto(product, *, name, description, price, category, image_filename, order, is_active):
    product.name = name
    product.description = description
    product.price = price
    product.category = category
    product.order = order or 0
    product.is_active = is_active

    # Só troca a imagem se uma nova foi enviada; senão mantém a atual.
    if image_filename:
        product.image_filename = image_filename

    db.session.commit()
    return product


def ativar_produto(product):
    product.is_active = True
    db.session.commit()


def desativar_produto(product):
    product.is_active = False
    db.session.commit()


def excluir_produto(product):
    """
    Remove o produto definitivamente. Se houver pedidos no histórico
    referenciando esse produto, o banco recusa a exclusão (chave
    estrangeira) e uma IntegrityError é levantada — a rota trata esse
    caso e orienta o usuário a desativar o produto em vez de excluir.
    """
    db.session.delete(product)
    db.session.commit()


# ==========================================================
# REAJUSTE DE PREÇOS (em massa ou individual)
# ==========================================================

def _aplicar_reajuste(preco_atual, modo, valor):
    if modo == "percent":
        novo_preco = preco_atual * (Decimal("1") + (valor / Decimal("100")))
    else:  # "fixed"
        novo_preco = preco_atual + valor

    # Nunca deixa o preço final ficar negativo
    if novo_preco < 0:
        novo_preco = Decimal("0.00")

    return novo_preco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def reajustar_precos(*, scope, modo, valor, product_id=None):
    """
    Aplica reajuste de preço por percentual ou valor fixo.
    scope="all"    -> aplica em todos os produtos cadastrados
    scope="single" -> aplica somente no produto indicado por product_id
    Retorna a quantidade de produtos atualizados.
    """
    if scope == "single":
        if not product_id:
            raise ValueError("Selecione um produto para aplicar o reajuste.")

        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")

        produtos = [product]
    else:
        produtos = Product.query.all()

    for produto in produtos:
        produto.price = _aplicar_reajuste(produto.price, modo, valor)

    db.session.commit()
    return len(produtos)

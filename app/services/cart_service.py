# cart_service.py

"""
Serviço de carrinho de compras baseado em sessão.

Mantém toda a lógica de manipulação do carrinho isolada das rotas,
para que orders.py e api.py fiquem finos (só validam entrada e chamam
estas funções).

IMPORTANTE sobre tipos: os valores monetários são guardados na sessão
como string (ex: "18.00"), não como Decimal. Isso porque o backend de
sessão (Flask-Session) pode usar serialização JSON dependendo da versão
e configuração, e Decimal não é serializável em JSON por padrão. A
conversão para Decimal é feita sempre que um cálculo é necessário.

O preço de cada item é SEMPRE lido do banco (tabela Product) no momento
de adicionar ao carrinho — nunca é aceito um preço vindo do cliente/JS.
"""
from decimal import Decimal, InvalidOperation
from flask import session

from ..models import Product

CART_SESSION_KEY = "cart"


def _cart_padrao():
    """Estrutura inicial vazia do carrinho, conforme especificação do módulo."""
    return {
        "items": [],
        "total": "0.00",
        "client_id": None,
        "client_data": {
            "name": "",
            "phone": "",
            "address": "",
            "neighborhood": "",
        },
        "delivery_fee": "0.00",
        "notes": "",
    }


def get_cart():
    """Retorna o carrinho atual da sessão, criando um vazio se ainda não existir."""
    if CART_SESSION_KEY not in session:
        session[CART_SESSION_KEY] = _cart_padrao()
    return session[CART_SESSION_KEY]


def _salvar(cart):
    """Persiste o carrinho na sessão e marca como modificado (necessário
    porque alterações em dicts/listas dentro da sessão não são detectadas
    automaticamente pelo Flask)."""
    session[CART_SESSION_KEY] = cart
    session.modified = True


def _to_decimal(value, campo="valor"):
    """Converte string/número para Decimal com tratamento de erro."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{campo} inválido: {value!r}")


def _recalcular_total(cart):
    """Recalcula o total do carrinho a partir dos itens. Sempre no servidor,
    nunca confia em total calculado no front-end."""
    total = sum((_to_decimal(item["subtotal"]) for item in cart["items"]), Decimal("0.00"))
    total += _to_decimal(cart.get("delivery_fee", "0.00"))
    cart["total"] = str(total.quantize(Decimal("0.01")))
    return cart


def add_item(product_id, quantity):
    """
    Adiciona um produto ao carrinho (soma a quantidade, se o produto já
    estiver no carrinho).
    """
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Quantidade inválida.")
    if quantity <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    product = Product.query.filter_by(id=int(product_id), is_active=True).first()
    if product is None:
        raise ValueError("Produto não encontrado ou indisponível.")

    cart = get_cart()

    for item in cart["items"]:
        if item["product_id"] == product.id:
            item["quantity"] += quantity
            item["subtotal"] = str(
                (_to_decimal(item["unit_price"]) * item["quantity"]).quantize(Decimal("0.01"))
            )
            break
    else:
        unit_price = product.price  # Decimal vindo do banco
        cart["items"].append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": str(unit_price),
            "subtotal": str((unit_price * quantity).quantize(Decimal("0.01"))),
        })

    _recalcular_total(cart)
    _salvar(cart)
    return cart


def remove_item(product_id):
    """Remove um produto do carrinho pelo id."""
    cart = get_cart()
    cart["items"] = [i for i in cart["items"] if i["product_id"] != int(product_id)]
    _recalcular_total(cart)
    _salvar(cart)
    return cart


def update_quantity(product_id, quantity):
    """Atualiza a quantidade de um item já presente no carrinho.
    Quantidade <= 0 remove o item."""
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Quantidade inválida.")

    if quantity <= 0:
        return remove_item(product_id)

    cart = get_cart()
    for item in cart["items"]:
        if item["product_id"] == int(product_id):
            item["quantity"] = quantity
            item["subtotal"] = str(
                (_to_decimal(item["unit_price"]) * quantity).quantize(Decimal("0.01"))
            )
            break
    else:
        raise ValueError("Item não encontrado no carrinho.")

    _recalcular_total(cart)
    _salvar(cart)
    return cart


def clear_cart():
    """Esvazia o carrinho, voltando à estrutura padrão."""
    _salvar(_cart_padrao())
    return get_cart()


def set_client_data(name, phone, address="", neighborhood="", client_id=None):
    """Atualiza os dados do cliente guardados no carrinho, antes de finalizar o pedido."""
    cart = get_cart()
    cart["client_id"] = client_id
    cart["client_data"] = {
        "name": (name or "").strip(),
        "phone": (phone or "").strip(),
        "address": (address or "").strip(),
        "neighborhood": (neighborhood or "").strip(),
    }
    _salvar(cart)
    return cart


def set_notes(notes):
    """Atualiza as observações do pedido guardadas no carrinho."""
    cart = get_cart()
    cart["notes"] = (notes or "").strip()
    _salvar(cart)
    return cart


def is_empty(cart=None):
    """Verifica se o carrinho não tem itens."""
    cart = cart or get_cart()
    return len(cart["items"]) == 0

"""
Rotas de API (JSON) do carrinho de compras e busca/cadastro de cliente.

Estas rotas são usadas via AJAX pelas páginas de pedido (balcão e público).
Não exigem login — tanto o balcão (já protegido por @login_required na
página que o carrega) quanto o pedido público usam o mesmo carrinho.
A proteção aqui é CSRF (obrigatório em todo POST, via header X-CSRFToken)
e rate limiting.
"""
from flask import Blueprint, jsonify, request
from ..extensions import limiter, db
from ..models import Client
from ..services import cart_service

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Quantidade mínima de dígitos exigida para buscar cliente por telefone.
# Evita varrer a tabela inteira a cada tecla digitada.
BUSCA_TELEFONE_MIN_DIGITOS = 3

# Quantidade máxima de resultados retornados na busca de cliente.
BUSCA_TELEFONE_LIMITE = 8


def _dados_requisicao():
    """
    Lê os dados da requisição aceitando tanto JSON quanto form-data,
    para não depender de como o JS do front-end decidir enviar.
    """
    dados = request.get_json(silent=True)
    if dados is None:
        dados = request.form
    return dados or {}


def _somente_digitos(texto):
    """Remove tudo que não for dígito (usado para normalizar telefone)."""
    return "".join(ch for ch in (texto or "") if ch.isdigit())


# ---------------------------------------------------------------------
# Carrinho
# ---------------------------------------------------------------------

@api_bp.post("/cart/add")
@limiter.limit("10 per minute")
def cart_add():
    dados = _dados_requisicao()
    product_id = dados.get("product_id")
    quantity = dados.get("quantity", 1)

    if not product_id:
        return jsonify({"erro": "product_id é obrigatório."}), 400

    try:
        cart = cart_service.add_item(product_id, quantity)
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400

    return jsonify({"ok": True, "cart": cart})


@api_bp.post("/cart/remove")
@limiter.limit("10 per minute")
def cart_remove():
    dados = _dados_requisicao()
    product_id = dados.get("product_id")

    if not product_id:
        return jsonify({"erro": "product_id é obrigatório."}), 400

    try:
        cart = cart_service.remove_item(product_id)
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400

    return jsonify({"ok": True, "cart": cart})


@api_bp.post("/cart/update")
@limiter.limit("10 per minute")
def cart_update():
    dados = _dados_requisicao()
    product_id = dados.get("product_id")
    quantity = dados.get("quantity")

    if not product_id or quantity is None:
        return jsonify({"erro": "product_id e quantity são obrigatórios."}), 400

    try:
        cart = cart_service.update_quantity(product_id, quantity)
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400

    return jsonify({"ok": True, "cart": cart})


@api_bp.post("/cart/clear")
@limiter.limit("10 per minute")
def cart_clear():
    cart = cart_service.clear_cart()
    return jsonify({"ok": True, "cart": cart})


@api_bp.get("/cart/get")
@limiter.limit("30 per minute")
def cart_get():
    cart = cart_service.get_cart()
    return jsonify({"ok": True, "cart": cart})


# ---------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------

@api_bp.get("/client/search")
@limiter.limit("5 per minute")
def client_search():
    telefone_digitado = _somente_digitos(request.args.get("phone"))

    if len(telefone_digitado) < BUSCA_TELEFONE_MIN_DIGITOS:
        return jsonify({
            "erro": f"Digite pelo menos {BUSCA_TELEFONE_MIN_DIGITOS} dígitos do telefone."
        }), 400

    # Busca parcial: telefone armazenado contém o trecho digitado.
    # Usa parâmetro do ORM (sem concatenação de string em SQL).
    clientes = (
        Client.query
        .filter(Client.phone.contains(telefone_digitado))
        .order_by(Client.name.asc())
        .limit(BUSCA_TELEFONE_LIMITE)
        .all()
    )

    resultado = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "neighborhood": c.neighborhood,
        }
        for c in clientes
    ]
    return jsonify({"ok": True, "clientes": resultado})


@api_bp.post("/client/create")
@limiter.limit("10 per minute")
def client_create():
    dados = _dados_requisicao()
    name = (dados.get("name") or "").strip()
    phone = (dados.get("phone") or "").strip()
    address = (dados.get("address") or "").strip()
    neighborhood = (dados.get("neighborhood") or "").strip()

    if not name or not phone:
        return jsonify({"erro": "Nome e telefone são obrigatórios."}), 400

    # Se já existe cliente com esse telefone (match exato), atualiza os dados.
    cliente = Client.query.filter_by(phone=phone).first()
    if cliente is None:
        cliente = Client(name=name, phone=phone, address=address, neighborhood=neighborhood)
        db.session.add(cliente)
    else:
        cliente.name = name
        cliente.address = address
        cliente.neighborhood = neighborhood

    db.session.commit()

    cart = cart_service.set_client_data(
        name=cliente.name,
        phone=cliente.phone,
        address=cliente.address,
        neighborhood=cliente.neighborhood,
        client_id=cliente.id,
    )

    return jsonify({
        "ok": True,
        "client": {
            "id": cliente.id,
            "name": cliente.name,
            "phone": cliente.phone,
            "address": cliente.address,
            "neighborhood": cliente.neighborhood,
        },
        "cart": cart,
    })

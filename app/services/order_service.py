# order_service.py

"""
Serviço de criação de pedidos a partir do carrinho da sessão.
"""
from decimal import Decimal
from ..models import db, Client, Order, OrderItem, Product


def find_or_create_client(name, phone, address="", neighborhood=""):
    """
    Busca cliente por telefone (match exato). Se existir, atualiza os
    dados (nome/endereço/bairro podem ter mudado). Se não existir, cria.
    """
    client = Client.query.filter_by(phone=phone).first()
    if client is None:
        client = Client(name=name, phone=phone, address=address, neighborhood=neighborhood)
        db.session.add(client)
    else:
        client.name = name
        client.address = address
        client.neighborhood = neighborhood
    return client


def create_order_from_cart(cart, user=None, delivery_fee=None):
    """
    Cria um pedido (Order + OrderItems) a partir do carrinho guardado na
    sessão.

    Importante: os preços são SEMPRE relidos do banco (tabela Product)
    neste momento, ignorando o preço que estava salvo no carrinho. Isso
    evita cobrar um valor desatualizado se o produto mudou de preço (ou
    foi desativado) entre o momento em que foi adicionado ao carrinho e
    agora.

    Levanta ValueError com mensagem amigável em caso de problema de
    negócio (carrinho vazio, dados de cliente faltando, produto que não
    existe mais) — a rota deve capturar e mostrar via flash().
    """
    if not cart.get("items"):
        raise ValueError("O carrinho está vazio.")

    client_data = cart.get("client_data") or {}
    name = (client_data.get("name") or "").strip()
    phone = (client_data.get("phone") or "").strip()
    if not name or not phone:
        raise ValueError("Nome e telefone do cliente são obrigatórios.")

    client = find_or_create_client(
        name=name,
        phone=phone,
        address=client_data.get("address", ""),
        neighborhood=client_data.get("neighborhood", ""),
    )
    db.session.flush()  # garante client.id disponível antes de criar o pedido

    taxa_entrega = Decimal(str(delivery_fee if delivery_fee is not None else cart.get("delivery_fee", "0.00")))

    order = Order(
        client_id=client.id,
        user_id=user.id if user else None,
        total=Decimal("0.00"),
        delivery_fee=taxa_entrega,
        notes=(cart.get("notes") or "").strip(),
        status="PENDENTE",
    )
    db.session.add(order)
    db.session.flush()  # garante order.id disponível antes de criar os itens

    total_itens = Decimal("0.00")
    for item in cart["items"]:
        product = Product.query.filter_by(id=item["product_id"], is_active=True).first()
        if product is None:
            db.session.rollback()
            nome_produto = item.get("product_name", item["product_id"])
            raise ValueError(f"O produto '{nome_produto}' não está mais disponível.")

        quantity = int(item["quantity"])
        unit_price = product.price  # preço atual, direto do banco
        subtotal = (unit_price * quantity).quantize(Decimal("0.01"))

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        db.session.add(order_item)
        total_itens += subtotal

    order.total = (total_itens + taxa_entrega).quantize(Decimal("0.01"))
    db.session.commit()
    return order

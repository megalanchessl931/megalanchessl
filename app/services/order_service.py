from decimal import Decimal
from ..models import db, Client, Order, OrderItem

def create_order(client_data, items, user=None):
    client = Client(**client_data)
    db.session.add(client)
    db.session.flush()

    order = Order(
        client_id=client.id,
        user_id=user.id if user else None,
        total=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        status="PENDENTE",
    )
    db.session.add(order)
    db.session.flush()

    total = Decimal("0.00")
    for item in items:
        subtotal = Decimal(item["unit_price"]) * int(item["quantity"])
        order_item = OrderItem(
            order_id=order.id,
            product_id=int(item["product_id"]),
            quantity=int(item["quantity"]),
            unit_price=Decimal(item["unit_price"]),
            subtotal=subtotal,
        )
        db.session.add(order_item)
        total += subtotal

    order.total = total
    db.session.commit()
    return order

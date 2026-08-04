from decimal import Decimal

from app.extensions import db
from app.models import Client, Order, OrderItem, Product, User


def test_create_user(app):
    user = User(
        username="carlos",
        email="carlos@example.com",
        is_admin=False,
    )
    user.set_password("senha123")

    with app.app_context():
        db.session.add(user)
        db.session.commit()

        saved_user = db.session.get(User, user.id)

        assert saved_user is not None
        assert saved_user.username == "carlos"
        assert saved_user.email == "carlos@example.com"
        assert saved_user.is_admin is False
        assert saved_user.password_hash != "senha123"


def test_user_password_is_valid(app):
    user = User(
        username="teste",
        email="teste@example.com",
    )
    user.set_password("senha-correta")

    assert user.check_password("senha-correta") is True
    assert user.check_password("senha-errada") is False


def test_create_product(app):
    product = Product(
        name="X-Burger Teste",
        description="Produto usado no teste",
        price=Decimal("25.90"),
        category="LANCHE",
    )

    with app.app_context():
        db.session.add(product)
        db.session.commit()

        saved_product = db.session.get(Product, product.id)

        assert saved_product is not None
        assert saved_product.name == "X-Burger Teste"
        assert saved_product.price == Decimal("25.90")
        assert saved_product.category == "LANCHE"
        assert saved_product.is_active is True
        assert saved_product.image_filename == "placeholder.jpg"


def test_create_client(app):
    client = Client(
        name="Cliente Teste",
        phone="51999999999",
        address="Rua de Teste, 100",
        neighborhood="Centro",
    )

    with app.app_context():
        db.session.add(client)
        db.session.commit()

        saved_client = db.session.get(Client, client.id)

        assert saved_client is not None
        assert saved_client.name == "Cliente Teste"
        assert saved_client.phone == "51999999999"
        assert saved_client.address == "Rua de Teste, 100"


def test_create_order_with_client(app):
    client = Client(
        name="Cliente Pedido",
        phone="51988888888",
    )

    order = Order(
        client=client,
        total=Decimal("30.00"),
        delivery_fee=Decimal("5.00"),
        status="PENDENTE",
    )

    with app.app_context():
        db.session.add(order)
        db.session.commit()

        saved_order = db.session.get(Order, order.id)

        assert saved_order is not None
        assert saved_order.client.name == "Cliente Pedido"
        assert saved_order.total == Decimal("30.00")
        assert saved_order.delivery_fee == Decimal("5.00")
        assert saved_order.status == "PENDENTE"


def test_create_order_item(app):
    product = Product(
        name="Produto Pedido",
        price=Decimal("12.50"),
        category="LANCHE",
    )

    order = Order(
        total=Decimal("25.00"),
    )

    item = OrderItem(
        order=order,
        product=product,
        quantity=2,
        unit_price=Decimal("12.50"),
        subtotal=Decimal("25.00"),
    )

    with app.app_context():
        db.session.add(order)
        db.session.commit()

        saved_item = db.session.get(OrderItem, item.id)

        assert saved_item is not None
        assert saved_item.quantity == 2
        assert saved_item.unit_price == Decimal("12.50")
        assert saved_item.subtotal == Decimal("25.00")
        assert saved_item.product.name == "Produto Pedido"
        assert saved_item.order.id == order.id


def test_order_items_relationship(app):
    product = Product(
        name="Produto Relacionamento",
        price=Decimal("10.00"),
        category="LANCHE",
    )

    order = Order(total=Decimal("20.00"))

    item = OrderItem(
        product=product,
        quantity=2,
        unit_price=Decimal("10.00"),
        subtotal=Decimal("20.00"),
    )

    order.items.append(item)

    with app.app_context():
        db.session.add(order)
        db.session.commit()

        saved_order = db.session.get(Order, order.id)

        assert len(saved_order.items) == 1
        assert saved_order.items[0].quantity == 2
        assert saved_order.items[0].product.name == "Produto Relacionamento"


def test_order_cascade_deletes_items(app):
    product = Product(
        name="Produto Cascade",
        price=Decimal("15.00"),
        category="LANCHE",
    )

    order = Order(total=Decimal("15.00"))

    item = OrderItem(
        product=product,
        quantity=1,
        unit_price=Decimal("15.00"),
        subtotal=Decimal("15.00"),
    )

    order.items.append(item)

    with app.app_context():
        db.session.add(order)
        db.session.commit()

        item_id = item.id
        order_id = order.id

        db.session.delete(order)
        db.session.commit()

        assert db.session.get(Order, order_id) is None
        assert db.session.get(OrderItem, item_id) is None

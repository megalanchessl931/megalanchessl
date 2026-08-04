from decimal import Decimal
from ..models import Product, db

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

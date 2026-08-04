from flask import Blueprint, render_template
from ..models import Product

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def index():
    return render_template("public/index.html")

@public_bp.get("/menu")
def menu():
    products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.order.asc(), Product.category.asc(), Product.name.asc())
        .all()
    )
    return render_template("public/menu.html", products=products)

@public_bp.get("/contato")
def contato():
    return render_template("public/contato.html")

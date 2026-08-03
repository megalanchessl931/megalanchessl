from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from ..models import Product, Order

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

@admin_bp.get("/")
@login_required
def dashboard():
    admin_required()
    return render_template(
        "admin/dashboard.html",
        product_count=Product.query.count(),
        order_count=Order.query.count(),
    )

@admin_bp.get("/pedidos")
@login_required
def pedidos_lista():
    admin_required()
    orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()
    return render_template("admin/pedidos_lista.html", orders=orders)

@admin_bp.get("/produtos")
@login_required
def produtos_crud():
    admin_required()
    products = Product.query.order_by(Product.order.asc(), Product.name.asc()).all()
    return render_template("admin/produtos_crud.html", products=products)

@admin_bp.route("/pedidos/<int:id>")
@login_required
def pedido_detalhe(id):
    from ..models import Order
    order = Order.query.get_or_404(id)
    return render_template("admin/pedido_detalhe.html", order=order)

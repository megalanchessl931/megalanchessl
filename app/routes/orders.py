# orders.py

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from ..extensions import limiter
from ..models import Product
from ..services import cart_service, order_service

orders_bp = Blueprint("orders", __name__, url_prefix="/pedidos")


class OrderForm(FlaskForm):
    """Formulário final de finalização do pedido (dados do cliente)."""
    name = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    phone = StringField("Telefone", validators=[DataRequired(), Length(max=20)])
    address = StringField("Endereço", validators=[Optional(), Length(max=200)])
    neighborhood = StringField("Bairro", validators=[Optional(), Length(max=50)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Finalizar pedido")


def _produtos_ativos():
    """Lista de produtos ativos para exibir no cardápio de montagem do pedido."""
    return (
        Product.query.filter_by(is_active=True)
        .order_by(Product.category.asc(), Product.order.asc(), Product.name.asc())
        .all()
    )


def _preencher_form_com_cliente_do_carrinho(form, cart):
    """
    Se já existem dados de cliente salvos no carrinho (ex: preenchidos
    via busca por telefone no /api/client/search), pré-popula o
    formulário na primeira exibição (GET), pra não perder o que a
    pessoa já buscou/preencheu via AJAX.
    """
    if form.is_submitted():
        return
    client_data = cart.get("client_data") or {}
    if client_data.get("name"):
        form.name.data = client_data.get("name")
    if client_data.get("phone"):
        form.phone.data = client_data.get("phone")
    if client_data.get("address"):
        form.address.data = client_data.get("address")
    if client_data.get("neighborhood"):
        form.neighborhood.data = client_data.get("neighborhood")


def _finalizar(template_name, endpoint_sucesso, user=None):
    """
    Lógica compartilhada entre balcão e pedido público: valida o
    formulário, atualiza os dados do cliente no carrinho, tenta criar o
    pedido e trata erros de negócio (carrinho vazio, produto que saiu
    do cardápio etc.) com mensagem amigável em vez de deixar estourar
    erro 500.
    """
    form = OrderForm()
    cart = cart_service.get_cart()
    _preencher_form_com_cliente_do_carrinho(form, cart)

    if form.validate_on_submit():
        cart_service.set_client_data(
            name=form.name.data,
            phone=form.phone.data,
            address=form.address.data,
            neighborhood=form.neighborhood.data,
            client_id=cart.get("client_id"),
        )
        cart_service.set_notes(form.notes.data)
        cart = cart_service.get_cart()

        try:
            order = order_service.create_order_from_cart(cart, user=user)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                template_name, form=form, cart=cart, products=_produtos_ativos()
            )

        cart_service.clear_cart()
        flash(f"Pedido #{order.id} registrado com sucesso.", "success")
        return redirect(url_for(endpoint_sucesso))

    return render_template(template_name, form=form, cart=cart, products=_produtos_ativos())


# ---------------------------------------------------------------------
# Balcão (uso interno, exige login)
# ---------------------------------------------------------------------

@orders_bp.route("/balcao", methods=["GET"])
@login_required
def pedido_balcao():
    form = OrderForm()
    cart = cart_service.get_cart()
    _preencher_form_com_cliente_do_carrinho(form, cart)
    return render_template(
        "orders/pedido_balcao.html", form=form, cart=cart, products=_produtos_ativos()
    )


@orders_bp.route("/balcao/finalizar", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def pedido_balcao_finalizar():
    return _finalizar("orders/pedido_balcao.html", "orders.pedido_balcao", user=current_user)


# ---------------------------------------------------------------------
# Pedido público (sem login)
# ---------------------------------------------------------------------

@orders_bp.route("/novo", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def pedido_publico():
    return _finalizar("orders/pedido_publico.html", "public.menu", user=None)

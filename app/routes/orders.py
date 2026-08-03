from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from ..extensions import limiter

from ..models import db, Client, Order, OrderItem, Product

orders_bp = Blueprint("orders", __name__, url_prefix="/pedidos")
class OrderForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    phone = StringField("Telefone", validators=[Optional(), Length(max=20)])
    address = StringField("Endereço", validators=[Optional(), Length(max=200)])
    neighborhood = StringField("Bairro", validators=[Optional(), Length(max=50)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Enviar pedido")

@orders_bp.route("/novo", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def pedido_publico():
    form = OrderForm()
    if form.validate_on_submit():
        # O carrinho real deve ser implementado no próximo módulo.
        flash("Estrutura de pedido pronta. O carrinho será conectado no próximo módulo.", "info")
        return redirect(url_for("public.menu"))
    return render_template("orders/pedido_publico.html", form=form)

@orders_bp.get("/balcao")
def pedido_balcao():
    # Balcão ainda não altera dados neste módulo base.
    return render_template("orders/pedido_balcao.html")

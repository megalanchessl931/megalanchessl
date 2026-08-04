# app/routes/admin.py

from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import (
    login_required,
    current_user,
)

from ..models import (
    db,
    Product,
    Order,
)

from ..forms import UserForm
from ..services.user_service import UserService
from ..services import printer_service

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
    admin_required()

    order = Order.query.get_or_404(id)

    return render_template(
        "admin/pedido_detalhe.html",
        order=order
    )
    
# ==========================================================
# USUÁRIOS
# ==========================================================

@admin_bp.route("/usuarios")
@login_required
def usuarios_lista():
    admin_required()

    usuarios = UserService.list_all()

    return render_template(
        "admin/usuarios_lista.html",
        usuarios=usuarios
    )


@admin_bp.route(
    "/usuarios/novo",
    methods=["GET", "POST"]
)
@login_required
def usuario_novo():

    admin_required()

    form = UserForm()

    if form.validate_on_submit():

        if not form.password.data:
            flash("A senha é obrigatória para novos usuários.", "error")
            return render_template(
                "admin/usuario_form.html",
                titulo="Novo Usuário",
                form=form
            )

        try:

            UserService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                is_admin=form.is_admin.data,
                is_active=form.is_active.data
            )

            flash(
                "Usuário cadastrado com sucesso.",
                "success"
            )

            return redirect(
                url_for("admin.usuarios_lista")
            )

        except ValueError as e:

            flash(
                str(e),
                "error"
            )

    elif request.method == "POST":

        print(form.errors)

        flash(
            "Existem erros no formulário.",
            "warning"
        )

    return render_template(
        "admin/usuario_form.html",
        titulo="Novo Usuário",
        form=form
    )
    
@admin_bp.route(
    "/usuarios/<int:user_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def usuario_editar(user_id):

    admin_required()

    usuario = UserService.get(user_id)

    if not usuario:
        abort(404)

    form = UserForm(obj=usuario)

    if form.validate_on_submit():

        try:

            UserService.update_user(
                user=usuario,
                username=form.username.data,
                email=form.email.data,
                is_admin=form.is_admin.data,
                is_active=form.is_active.data
            )

            flash(
                "Usuário atualizado com sucesso.",
                "success"
            )

            return redirect(
                url_for("admin.usuarios_lista")
            )

        except ValueError as e:

            flash(
                str(e),
                "error"
            )

    return render_template(
        "admin/usuario_form.html",
        titulo="Editar Usuário",
        form=form
    )

# ==========================================================
# ALTERAR SENHA
# ==========================================================

@admin_bp.route(
    "/usuarios/<int:user_id>/senha",
    methods=["GET", "POST"]
)
@login_required
def usuario_senha(user_id):

    admin_required()

    usuario = UserService.get(user_id)

    if not usuario:
        abort(404)

    form = UserForm()

    if request.method == "POST":

        if not form.password.data:

            flash(
                "Informe a nova senha.",
                "warning"
            )

        elif form.password.data != form.confirm_password.data:

            flash(
                "As senhas não conferem.",
                "error"
            )

        else:

            UserService.change_password(
                usuario,
                form.password.data
            )

            flash(
                "Senha alterada com sucesso.",
                "success"
            )

            return redirect(
                url_for("admin.usuarios_lista")
            )

    return render_template(
        "admin/usuario_senha.html",
        usuario=usuario,
        form=form
    )

# ==========================================================
# ATIVAR USUÁRIO
# ==========================================================

@admin_bp.route("/usuarios/<int:user_id>/ativar")
@login_required
def usuario_ativar(user_id):

    admin_required()

    usuario = UserService.get(user_id)

    if not usuario:
        abort(404)

    UserService.activate(usuario)

    flash(
        "Usuário ativado com sucesso.",
        "success"
    )

    return redirect(
        url_for("admin.usuarios_lista")
    )


# ==========================================================
# DESATIVAR USUÁRIO
# ==========================================================

@admin_bp.route("/usuarios/<int:user_id>/desativar")
@login_required
def usuario_desativar(user_id):

    admin_required()

    usuario = UserService.get(user_id)

    if not usuario:
        abort(404)

    # Não permite desativar o próprio usuário
    if usuario.id == current_user.id:

        flash(
            "Você não pode desativar seu próprio usuário.",
            "error"
        )

        return redirect(
            url_for("admin.usuarios_lista")
        )

    try:

        UserService.deactivate(usuario)

        flash(
            "Usuário desativado com sucesso.",
            "success"
        )

    except ValueError as e:

        flash(
            str(e),
            "error"
        )

    return redirect(
        url_for("admin.usuarios_lista")
    )


# ==========================================================
# STATUS E IMPRESSÃO DO PEDIDO
# ==========================================================

STATUS_PEDIDO_VALIDOS = {"PENDENTE", "EM_PREPARO", "ENTREGUE", "CANCELADO"}


@admin_bp.route("/pedidos/<int:id>/status", methods=["POST"])
@login_required
def atualizar_status_pedido(id):
    admin_required()

    order = Order.query.get_or_404(id)
    novo_status = request.form.get("status", "")

    if novo_status not in STATUS_PEDIDO_VALIDOS:
        flash("Status inválido.", "error")
        return redirect(url_for("admin.pedido_detalhe", id=id))

    order.status = novo_status
    db.session.commit()

    flash(f"Status do pedido #{order.id} atualizado para {novo_status}.", "success")
    return redirect(url_for("admin.pedido_detalhe", id=id))


@admin_bp.route("/pedidos/<int:id>/imprimir", methods=["POST"])
@login_required
def imprimir_pedido(id):
    admin_required()

    order = Order.query.get_or_404(id)

    order_data = {"id": order.id, "total": str(order.total)}
    sucesso = printer_service.imprimir_cupom(order_data)

    if sucesso:
        flash(f"Pedido #{order.id} enviado para a impressora.", "success")
    else:
        flash("Impressora não configurada ou indisponível (PRINT_DEVICE).", "warning")

    return redirect(url_for("admin.pedido_detalhe", id=id))

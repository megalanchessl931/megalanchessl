# app/routes/admin.py

import os
import csv
import io
from datetime import datetime, date
from decimal import Decimal

from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    Response,
    send_file,
)

from flask_login import (
    login_required,
    current_user,
)

from sqlalchemy.exc import IntegrityError

from ..models import (
    db,
    Product,
    Order,
)

from ..forms import UserForm, ProductForm, PriceUpdateForm, ReportFilterForm
from ..services.user_service import UserService
from ..services import printer_service
from ..services import product_service
from ..services import report_service
from ..services import pdf_service

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

# ==========================================================
# PRODUTOS
# ==========================================================

@admin_bp.get("/produtos")
@login_required
def produtos_crud():
    admin_required()

    # Colunas que podem ser usadas para ordenar, mapeadas para o
    # campo real do modelo. Uma "lista branca" evita que alguém
    # passe um valor arbitrário em ?sort= e quebre a consulta.
    COLUNAS_ORDENACAO = {
        "id": Product.id,
        "name": Product.name,
        "category": Product.category,
        "price": Product.price,
        "order": Product.order,
        "is_active": Product.is_active,
    }

    sort = request.args.get("sort", "order")
    direction = request.args.get("dir", "asc")

    coluna = COLUNAS_ORDENACAO.get(sort, Product.order)

    if direction == "desc":
        coluna = coluna.desc()
    else:
        direction = "asc"  # normaliza qualquer valor inválido para "asc"

    # Critério de desempate estável: nome, pra produtos com o mesmo
    # valor na coluna ordenada não ficarem "pulando" de posição.
    products = Product.query.order_by(coluna, Product.name.asc()).all()

    return render_template(
        "admin/produtos_crud.html",
        products=products,
        sort=sort,
        direction=direction,
    )


@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@login_required
def produto_novo():
    admin_required()

    form = ProductForm()

    if form.validate_on_submit():

        image_filename = None
        if form.image.data:
            image_filename = product_service.salvar_imagem_produto(
                form.image.data,
                current_app.config["UPLOAD_FOLDER_PRODUTOS"]
            )

        try:
            product_service.criar_produto(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,
                image_filename=image_filename,
                order=form.order.data,
                is_active=form.is_active.data,
            )

            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("admin.produtos_crud"))

        except IntegrityError:
            db.session.rollback()
            flash("Já existe um produto cadastrado com esse nome.", "error")

    elif request.method == "POST":
        flash("Existem erros no formulário.", "warning")

    return render_template(
        "admin/produto_form.html",
        titulo="Novo Produto",
        form=form,
        product=None
    )


@admin_bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@login_required
def produto_editar(product_id):
    admin_required()

    product = Product.query.get_or_404(product_id)

    form = ProductForm(obj=product)

    if form.validate_on_submit():

        image_filename = None
        if form.image.data:
            image_filename = product_service.salvar_imagem_produto(
                form.image.data,
                current_app.config["UPLOAD_FOLDER_PRODUTOS"]
            )

        try:
            product_service.atualizar_produto(
                product,
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,
                image_filename=image_filename,
                order=form.order.data,
                is_active=form.is_active.data,
            )

            flash("Produto atualizado com sucesso.", "success")
            return redirect(url_for("admin.produtos_crud"))

        except IntegrityError:
            db.session.rollback()
            flash("Já existe um produto cadastrado com esse nome.", "error")

    elif request.method == "GET":
        # Preenche o campo de preço com o valor atual (obj= não cobre DecimalField com places)
        form.price.data = product.price

    return render_template(
        "admin/produto_form.html",
        titulo="Editar Produto",
        form=form,
        product=product
    )


@admin_bp.route("/produtos/<int:product_id>/ativar")
@login_required
def produto_ativar(product_id):
    admin_required()

    product = Product.query.get_or_404(product_id)
    product_service.ativar_produto(product)

    flash("Produto ativado com sucesso.", "success")
    return redirect(url_for("admin.produtos_crud"))


@admin_bp.route("/produtos/<int:product_id>/desativar")
@login_required
def produto_desativar(product_id):
    admin_required()

    product = Product.query.get_or_404(product_id)
    product_service.desativar_produto(product)

    flash("Produto desativado com sucesso.", "success")
    return redirect(url_for("admin.produtos_crud"))


@admin_bp.route("/produtos/<int:product_id>/excluir", methods=["POST"])
@login_required
def produto_excluir(product_id):
    admin_required()

    product = Product.query.get_or_404(product_id)

    try:
        product_service.excluir_produto(product)
        flash("Produto excluído com sucesso.", "success")

    except IntegrityError:
        db.session.rollback()
        flash(
            "Esse produto já tem pedidos no histórico e não pode ser excluído. "
            "Desative o produto em vez de excluir.",
            "error"
        )

    return redirect(url_for("admin.produtos_crud"))


@admin_bp.route("/produtos/reajustar-precos", methods=["GET", "POST"])
@login_required
def produtos_reajustar_precos():
    admin_required()

    form = PriceUpdateForm()

    produtos = Product.query.order_by(Product.name.asc()).all()
    form.product_id.choices = [("", "Selecione um produto")] + [
        (str(p.id), p.name) for p in produtos
    ]

    if form.validate_on_submit():

        if form.scope.data == "single" and not form.product_id.data:
            flash("Selecione um produto para aplicar o reajuste.", "warning")

        else:
            try:
                qtd = product_service.reajustar_precos(
                    scope=form.scope.data,
                    modo=form.mode.data,
                    valor=form.value.data,
                    product_id=form.product_id.data or None,
                )

                flash(f"Reajuste aplicado em {qtd} produto(s).", "success")
                return redirect(url_for("admin.produtos_crud"))

            except ValueError as e:
                flash(str(e), "error")

    return render_template(
        "admin/produtos_reajuste.html",
        form=form
    )

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
                is_active=form.is_active.data,
                phone=form.phone.data,
                notes=form.notes.data
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
                is_active=form.is_active.data,
                phone=form.phone.data,
                notes=form.notes.data
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


# ==========================================================
# RELATÓRIOS
# ==========================================================

def _resolver_periodo(form):

#    Lê data_inicio/data_fim do formulário de filtro. Se estiverem
#    vazios (primeira visita à página, sem filtro aplicado ainda),
#    usa o período padrão (mês atual).

    if form.data_inicio.data and form.data_fim.data:
        return form.data_inicio.data, form.data_fim.data

    return report_service.periodo_padrao()



@admin_bp.route("/relatorios", methods=["GET"])
@login_required
def relatorios():
    admin_required()

    form = ReportFilterForm(request.args, meta={"csrf": False})

    data_inicio, data_fim = _resolver_periodo(form)

    resumo = report_service.resumo(data_inicio, data_fim)
    vendas_periodo = report_service.vendas_por_periodo(data_inicio, data_fim)
    produtos_top = report_service.produtos_mais_vendidos(data_inicio, data_fim)
    vendas_categoria = report_service.vendas_por_categoria(data_inicio, data_fim)

    return render_template(
        "admin/relatorios.html",
        form=form,
        data_inicio=data_inicio,
        data_fim=data_fim,
        resumo=resumo,
        vendas_periodo=vendas_periodo,
        produtos_top=produtos_top,
        vendas_categoria=vendas_categoria,
    )


def _parse_data_export(nome_param):

#    
#    Faz o parse de uma data vinda da querystring nas rotas de
#    exportação CSV (que não usam WTForms, pra manter o link simples).
#    
    valor = request.args.get(nome_param)

    if not valor:
        return None

    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def _periodo_export():
    data_inicio = _parse_data_export("data_inicio")
    data_fim = _parse_data_export("data_fim")

    if not data_inicio or not data_fim:
        data_inicio, data_fim = report_service.periodo_padrao()

    return data_inicio, data_fim


def _csv_response(linhas_cabecalho, linhas_dados, nome_arquivo):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")

    writer.writerow(linhas_cabecalho)
    for linha in linhas_dados:
        writer.writerow(linha)

    # utf-8-sig garante que o Excel abra os acentos corretamente
    conteudo = "\ufeff" + buffer.getvalue()

    return Response(
        conteudo,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={nome_arquivo}"
        }
    )


@admin_bp.get("/relatorios/exportar/vendas-por-periodo.csv")
@login_required
def exportar_vendas_periodo():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.vendas_por_periodo(data_inicio, data_fim)

    dados = [
        [linha.dia.strftime("%d/%m/%Y"), f"{linha.total:.2f}", linha.qtd_pedidos]
        for linha in linhas
    ]

    return _csv_response(
        ["Data", "Total Faturado (R$)", "Qtd Pedidos"],
        dados,
        "vendas_por_periodo.csv"
    )


@admin_bp.get("/relatorios/exportar/produtos-mais-vendidos.csv")
@login_required
def exportar_produtos_top():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.produtos_mais_vendidos(data_inicio, data_fim)

    dados = [
        [linha.nome, linha.categoria, linha.quantidade, f"{linha.total:.2f}"]
        for linha in linhas
    ]

    return _csv_response(
        ["Produto", "Categoria", "Quantidade Vendida", "Total Faturado (R$)"],
        dados,
        "produtos_mais_vendidos.csv"
    )


@admin_bp.get("/relatorios/exportar/vendas-por-categoria.csv")
@login_required
def exportar_vendas_categoria():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.vendas_por_categoria(data_inicio, data_fim)

    dados = [
        [linha.categoria, linha.quantidade, f"{linha.total:.2f}"]
        for linha in linhas
    ]

    return _csv_response(
        ["Categoria", "Quantidade Vendida", "Total Faturado (R$)"],
        dados,
        "vendas_por_categoria.csv"
    )


# ==========================================================
# RELATÓRIOS — VISUALIZAÇÃO EM PDF
# ==========================================================

def _caminho_fonte_ahkio():
    return os.path.join(current_app.root_path, "static", "fonts", "ahkio.ttf")


@admin_bp.get("/relatorios/visualizar/vendas-por-periodo.pdf")
@login_required
def visualizar_pdf_vendas_periodo():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.vendas_por_periodo(data_inicio, data_fim)

    buffer = pdf_service.gerar_pdf_vendas_periodo(
        data_inicio, data_fim, linhas, _caminho_fonte_ahkio()
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name="vendas_por_periodo.pdf",
    )


@admin_bp.get("/relatorios/visualizar/produtos-mais-vendidos.pdf")
@login_required
def visualizar_pdf_produtos_top():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.produtos_mais_vendidos(data_inicio, data_fim)

    buffer = pdf_service.gerar_pdf_produtos_top(
        data_inicio, data_fim, linhas, _caminho_fonte_ahkio()
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name="produtos_mais_vendidos.pdf",
    )


@admin_bp.get("/relatorios/visualizar/vendas-por-categoria.pdf")
@login_required
def visualizar_pdf_vendas_categoria():
    admin_required()

    data_inicio, data_fim = _periodo_export()
    linhas = report_service.vendas_por_categoria(data_inicio, data_fim)

    buffer = pdf_service.gerar_pdf_vendas_categoria(
        data_inicio, data_fim, linhas, _caminho_fonte_ahkio()
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name="vendas_por_categoria.pdf",
    )
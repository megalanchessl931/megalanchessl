# app/routes/reports.py

import csv
import io
import os

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    Response,
    current_app,
    send_file,
)

from flask_login import (
    login_required,
    current_user,
)

from ..forms.report_form import ReportFilterForm

from ..services import pdf_service
from ..services.report_vendas_service import ReportVendasService


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/admin/relatorios"
)

report_vendas_service = ReportVendasService()


# ==========================================================
# CONTROLE DE ACESSO
# ==========================================================

def admin_required():

    if (
        not current_user.is_authenticated
        or
        not current_user.is_admin
    ):
        abort(403)


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def _resolver_periodo(form):
    """
    Resolve o período informado pelo usuário.
    Caso não exista filtro, utiliza o mês atual.
    """

    if form.data_inicio.data and form.data_fim.data:

        return (
            form.data_inicio.data,
            form.data_fim.data
        )

    return report_vendas_service.periodo_padrao()


def _parse_data_export(nome_param):
    """
    Faz o parse das datas vindas pela querystring.
    """

    valor = request.args.get(nome_param)

    if not valor:
        return None

    try:

        return datetime.strptime(
            valor,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return None


def _periodo_export():

    data_inicio = _parse_data_export(
        "data_inicio"
    )

    data_fim = _parse_data_export(
        "data_fim"
    )

    if not data_inicio or not data_fim:

        data_inicio, data_fim = (
            report_vendas_service.periodo_padrao()
        )

    return (
        data_inicio,
        data_fim
    )


def _csv_response(
    linhas_cabecalho,
    linhas_dados,
    nome_arquivo
):

    buffer = io.StringIO()

    writer = csv.writer(
        buffer,
        delimiter=";"
    )

    writer.writerow(
        linhas_cabecalho
    )

    for linha in linhas_dados:

        writer.writerow(
            linha
        )

    conteudo = (
        "\ufeff"
        + buffer.getvalue()
    )

    return Response(

        conteudo,

        mimetype="text/csv",

        headers={

            "Content-Disposition":
            f"attachment; filename={nome_arquivo}"

        }

    )


def _caminho_fonte_ahkio():

    return os.path.join(

        current_app.root_path,

        "static",

        "fonts",

        "ahkio.ttf",

    )


# ==========================================================
# DASHBOARD DOS RELATÓRIOS
# ==========================================================

@reports_bp.route("/")
@login_required
def dashboard():

    admin_required()

    return render_template(

        "reports/dashboard.html"

    )


# ==========================================================
# RELATÓRIO DE VENDAS
# ==========================================================

@reports_bp.route(
    "/vendas",
    methods=["GET"]
)
@login_required
def vendas():

    admin_required()

    form = ReportFilterForm(

        request.args,

        meta={
            "csrf": False
        }

    )

    data_inicio, data_fim = (

        _resolver_periodo(form)

    )

    resumo = report_vendas_service.resumo(

        data_inicio,

        data_fim

    )

    vendas_periodo = (

        report_vendas_service.vendas_por_periodo(

            data_inicio,

            data_fim

        )

    )

    produtos_top = (

        report_vendas_service.produtos_mais_vendidos(

            data_inicio,

            data_fim

        )

    )

    vendas_categoria = (

        report_vendas_service.vendas_por_categoria(

            data_inicio,

            data_fim

        )

    )

    return render_template(

        "reports/vendas.html",

        form=form,

        resumo=resumo,

        vendas_periodo=vendas_periodo,

        produtos_top=produtos_top,

        vendas_categoria=vendas_categoria,

        data_inicio=data_inicio,

        data_fim=data_fim,

    )

# ==========================================================
# EXPORTAÇÃO CSV
# ==========================================================

@reports_bp.get("/exportar/vendas-por-periodo.csv")
@login_required
def exportar_vendas_periodo():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.vendas_por_periodo(
        data_inicio,
        data_fim
    )

    dados = [

        [
            linha.dia.strftime("%d/%m/%Y"),
            f"{linha.total:.2f}",
            linha.qtd_pedidos,
        ]

        for linha in linhas

    ]

    return _csv_response(

        ["Data", "Total Faturado (R$)", "Qtd Pedidos"],

        dados,

        "vendas_por_periodo.csv",

    )


@reports_bp.get("/exportar/produtos-mais-vendidos.csv")
@login_required
def exportar_produtos_top():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.produtos_mais_vendidos(
        data_inicio,
        data_fim
    )

    dados = [

        [
            linha.nome,
            linha.categoria,
            linha.quantidade,
            f"{linha.total:.2f}",
        ]

        for linha in linhas

    ]

    return _csv_response(

        [
            "Produto",
            "Categoria",
            "Quantidade Vendida",
            "Total Faturado (R$)",
        ],

        dados,

        "produtos_mais_vendidos.csv",

    )


@reports_bp.get("/exportar/vendas-por-categoria.csv")
@login_required
def exportar_vendas_categoria():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.vendas_por_categoria(
        data_inicio,
        data_fim
    )

    dados = [

        [
            linha.categoria,
            linha.quantidade,
            f"{linha.total:.2f}",
        ]

        for linha in linhas

    ]

    return _csv_response(

        [
            "Categoria",
            "Quantidade Vendida",
            "Total Faturado (R$)",
        ],

        dados,

        "vendas_por_categoria.csv",

    )


# ==========================================================
# PDF
# ==========================================================

@reports_bp.get("/visualizar/vendas-por-periodo.pdf")
@login_required
def visualizar_pdf_vendas_periodo():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.vendas_por_periodo(
        data_inicio,
        data_fim
    )

    buffer = pdf_service.gerar_pdf_vendas_periodo(

        data_inicio,

        data_fim,

        linhas,

        _caminho_fonte_ahkio(),

    )

    return send_file(

        buffer,

        mimetype="application/pdf",

        as_attachment=False,

        download_name="vendas_por_periodo.pdf",

    )


@reports_bp.get("/visualizar/produtos-mais-vendidos.pdf")
@login_required
def visualizar_pdf_produtos_top():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.produtos_mais_vendidos(
        data_inicio,
        data_fim
    )

    buffer = pdf_service.gerar_pdf_produtos_top(

        data_inicio,

        data_fim,

        linhas,

        _caminho_fonte_ahkio(),

    )

    return send_file(

        buffer,

        mimetype="application/pdf",

        as_attachment=False,

        download_name="produtos_mais_vendidos.pdf",

    )


@reports_bp.get("/visualizar/vendas-por-categoria.pdf")
@login_required
def visualizar_pdf_vendas_categoria():

    admin_required()

    data_inicio, data_fim = _periodo_export()

    linhas = report_vendas_service.vendas_por_categoria(
        data_inicio,
        data_fim
    )

    buffer = pdf_service.gerar_pdf_vendas_categoria(

        data_inicio,

        data_fim,

        linhas,

        _caminho_fonte_ahkio(),

    )

    return send_file(

        buffer,

        mimetype="application/pdf",

        as_attachment=False,

        download_name="vendas_por_categoria.pdf",

    )


# ==========================================================
# CLIENTES
# ==========================================================

@reports_bp.route("/clientes")
@login_required
def clientes():

    admin_required()

    return render_template(
        "reports/clientes.html"
    )


# ==========================================================
# PRODUTOS
# ==========================================================

@reports_bp.route("/produtos")
@login_required
def produtos():

    admin_required()

    return render_template(
        "reports/produtos.html"
    )


# ==========================================================
# FATURAMENTO
# ==========================================================

@reports_bp.route("/faturamento")
@login_required
def faturamento():

    admin_required()

    return render_template(
        "reports/faturamento.html"
    )


# ==========================================================
# FORNECEDORES
# ==========================================================

@reports_bp.route("/fornecedores")
@login_required
def fornecedores():

    admin_required()

    return render_template(
        "reports/fornecedores.html"
    )

# ==========================================================
# RELATÓRIOS VENDAS
# ==========================================================

@reports_bp.route(
    "/vendas/periodo",
    methods=["GET"]
)
@login_required
def vendas_periodo():

    admin_required()

    form = ReportFilterForm(
        request.args,
        meta={"csrf": False}
    )

    data_inicio, data_fim = _resolver_periodo(form)

    resumo = report_vendas_service.resumo(
        data_inicio,
        data_fim
    )

    vendas_periodo = report_vendas_service.vendas_por_periodo(
        data_inicio,
        data_fim
    )

    return render_template(
        "reports/vendas_periodo.html",
        form=form,
        data_inicio=data_inicio,
        data_fim=data_fim,
        resumo=resumo,
        vendas_periodo=vendas_periodo,
    )


@reports_bp.route(
    "/vendas/produtos",
    methods=["GET"]
)
@login_required
def vendas_produtos():

    admin_required()

    form = ReportFilterForm(
        request.args,
        meta={"csrf": False}
    )

    data_inicio, data_fim = _resolver_periodo(form)

    produtos_top = report_vendas_service.produtos_mais_vendidos(
        data_inicio,
        data_fim
    )

    return render_template(
        "reports/vendas_produtos.html",
        form=form,
        data_inicio=data_inicio,
        data_fim=data_fim,
        produtos_top=produtos_top,
    )


@reports_bp.route(
    "/vendas/categoria",
    methods=["GET"]
)
@login_required
def vendas_categoria():

    admin_required()

    form = ReportFilterForm(
        request.args,
        meta={"csrf": False}
    )

    data_inicio, data_fim = _resolver_periodo(form)

    vendas_categoria = report_vendas_service.vendas_por_categoria(
        data_inicio,
        data_fim
    )

    return render_template(
        "reports/vendas_categoria.html",
        form=form,
        data_inicio=data_inicio,
        data_fim=data_fim,
        vendas_categoria=vendas_categoria,
    )

# ==========================================================
# RELATÓRIOS CLIENTES
# ==========================================================

@reports_bp.route("/clientes/cadastrados")
@login_required
def clientes_cadastrados():

    admin_required()

    return render_template(
        "reports/clientes_cadastrados.html"
    )


@reports_bp.route("/clientes/frequentes")
@login_required
def clientes_frequentes():

    admin_required()

    return render_template(
        "reports/clientes_frequentes.html"
    )


@reports_bp.route("/clientes/ticket")
@login_required
def clientes_ticket():

    admin_required()

    return render_template(
        "reports/clientes_ticket.html"
    )

# ==========================================================
# RELATÓRIOS PRODUTOS
# ==========================================================

@reports_bp.route("/produtos/mais-vendidos")
@login_required
def produtos_mais_vendidos():

    admin_required()

    return render_template(
        "reports/produtos_mais_vendidos.html"
    )


@reports_bp.route("/produtos/menos-vendidos")
@login_required
def produtos_menos_vendidos():

    admin_required()

    return render_template(
        "reports/produtos_menos_vendidos.html"
    )


@reports_bp.route("/produtos/sem-venda")
@login_required
def produtos_sem_venda():

    admin_required()

    return render_template(
        "reports/produtos_sem_venda.html"
    )


# ==========================================================
# RELATÓRIOS FATURAMENTO
# ==========================================================

@reports_bp.route("/faturamento/diario")
@login_required
def faturamento_diario():

    admin_required()

    return render_template(
        "reports/faturamento_diario.html"
    )


@reports_bp.route("/faturamento/mensal")
@login_required
def faturamento_mensal():

    admin_required()

    return render_template(
        "reports/faturamento_mensal.html"
    )


@reports_bp.route("/faturamento/anual")
@login_required
def faturamento_anual():

    admin_required()

    return render_template(
        "reports/faturamento_anual.html"
    )


@reports_bp.route("/faturamento/pagamentos")
@login_required
def faturamento_pagamentos():

    admin_required()

    return render_template(
        "reports/faturamento_pagamentos.html"
    )


# ==========================================================
# RELATÓRIOS FORNECEDORES
# ==========================================================

@reports_bp.route("/fornecedores/compras")
@login_required
def fornecedores_compras():

    admin_required()

    return render_template(
        "reports/fornecedores_compras.html"
    )
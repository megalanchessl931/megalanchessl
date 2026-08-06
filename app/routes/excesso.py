
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
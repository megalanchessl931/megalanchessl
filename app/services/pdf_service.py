# pdf_service.py

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Cores da marca (mesmas usadas no admin.css)
COR_PRIMARIA = colors.HexColor("#6F1D1B")
COR_VERMELHO_LOGO = colors.HexColor("#F71C18")
COR_AMARELO_LOGO = colors.HexColor("#FFEB3B")
COR_TEXTO = colors.HexColor("#2E2E2E")
COR_LINHA_ALTERNADA = colors.HexColor("#F4F5F7")
COR_GRADE = colors.HexColor("#CCCCCC")

_FONTE_AHKIO_REGISTRADA = False


def _registrar_fonte_ahkio(caminho_fonte):
    """
    Registra a fonte Ahkio no reportlab uma única vez por processo.
    Sem isso, o reportlab não sabe desenhar texto com font_name="Ahkio".
    """
    global _FONTE_AHKIO_REGISTRADA

    if not _FONTE_AHKIO_REGISTRADA:
        pdfmetrics.registerFont(TTFont("Ahkio", caminho_fonte))
        _FONTE_AHKIO_REGISTRADA = True


def _desenhar_cabecalho(canvas_obj, doc, titulo, periodo_texto, caminho_fonte):
    """
    Desenha o cabeçalho no topo de cada página do PDF: a logo
    "MEGA LANCHES" (texto vermelho com uma cópia amarela deslocada
    atrás, igual ao cabeçalho do painel admin), o título do relatório
    e o período filtrado.
    """
    _registrar_fonte_ahkio(caminho_fonte)

    canvas_obj.saveState()

    largura_pagina, altura_pagina = doc.pagesize
    x = 20 * mm
    y = altura_pagina - 25 * mm

    canvas_obj.setFont("Ahkio", 30)

    # Camada amarela, deslocada na diagonal (efeito "duas imagens sobrepostas")
    canvas_obj.setFillColor(COR_AMARELO_LOGO)
    canvas_obj.drawString(x + 1.3, y - 1.3, "MEGA LANCHES")

    # Camada vermelha por cima
    canvas_obj.setFillColor(COR_VERMELHO_LOGO)
    canvas_obj.drawString(x, y, "MEGA LANCHES")

    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.setFillColor(COR_TEXTO)
    canvas_obj.drawString(x, y - 11 * mm, titulo)

    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(x, y - 17 * mm, periodo_texto)

    canvas_obj.setStrokeColor(COR_PRIMARIA)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(x, y - 21 * mm, largura_pagina - x, y - 21 * mm)

    canvas_obj.restoreState()


def _gerar_pdf_tabela(*, titulo, periodo_texto, cabecalho, linhas, larguras, caminho_fonte):
    """
    Monta um PDF genérico de uma tabela de relatório: cabeçalho da
    marca no topo de toda página + a tabela de dados no corpo.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=45 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    dados = [cabecalho] + linhas

    tabela = Table(dados, colWidths=larguras, repeatRows=1)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_GRADE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_LINHA_ALTERNADA]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    def _desenhar_pagina(canvas_obj, doc_obj):
        _desenhar_cabecalho(canvas_obj, doc_obj, titulo, periodo_texto, caminho_fonte)

    doc.build(
        [tabela],
        onFirstPage=_desenhar_pagina,
        onLaterPages=_desenhar_pagina,
    )

    buffer.seek(0)
    return buffer


def _texto_periodo(data_inicio, data_fim):
    return f"Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"


def gerar_pdf_vendas_periodo(data_inicio, data_fim, linhas_query, caminho_fonte):
    linhas = [
        [linha.dia.strftime("%d/%m/%Y"), str(linha.qtd_pedidos), f"R$ {linha.total:.2f}"]
        for linha in linhas_query
    ]

    return _gerar_pdf_tabela(
        titulo="Relatório de Vendas por Período",
        periodo_texto=_texto_periodo(data_inicio, data_fim),
        cabecalho=["Data", "Pedidos", "Total Faturado"],
        linhas=linhas,
        larguras=[50 * mm, 40 * mm, 50 * mm],
        caminho_fonte=caminho_fonte,
    )


def gerar_pdf_produtos_top(data_inicio, data_fim, linhas_query, caminho_fonte):
    linhas = [
        [linha.nome, linha.categoria, str(linha.quantidade), f"R$ {linha.total:.2f}"]
        for linha in linhas_query
    ]

    return _gerar_pdf_tabela(
        titulo="Relatório de Produtos Mais Vendidos",
        periodo_texto=_texto_periodo(data_inicio, data_fim),
        cabecalho=["Produto", "Categoria", "Quantidade", "Total Faturado"],
        linhas=linhas,
        larguras=[55 * mm, 35 * mm, 25 * mm, 35 * mm],
        caminho_fonte=caminho_fonte,
    )


def gerar_pdf_vendas_categoria(data_inicio, data_fim, linhas_query, caminho_fonte):
    linhas = [
        [linha.categoria, str(linha.quantidade), f"R$ {linha.total:.2f}"]
        for linha in linhas_query
    ]

    return _gerar_pdf_tabela(
        titulo="Relatório de Vendas por Categoria",
        periodo_texto=_texto_periodo(data_inicio, data_fim),
        cabecalho=["Categoria", "Quantidade", "Total Faturado"],
        linhas=linhas,
        larguras=[60 * mm, 40 * mm, 50 * mm],
        caminho_fonte=caminho_fonte,
    )
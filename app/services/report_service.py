from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import func

from ..models import db, Order, OrderItem, Product

# Pedidos cancelados não entram no faturamento nem nos rankings,
# mas são contados à parte no resumo (pra não "sumir" da visão do Carlos).
STATUS_CANCELADO = "CANCELADO"


def periodo_padrao():
    """
    Quando o usuário não escolhe um período, usamos o mês corrente
    (do dia 1 até hoje) como padrão.
    """
    hoje = datetime.now(timezone.utc).date()
    inicio = hoje.replace(day=1)
    return inicio, hoje


def _limites_datetime(data_inicio, data_fim):
    """
    Converte as datas (sem hora) do filtro em limites de datetime,
    cobrindo o dia inteiro de data_fim (00:00 até 23:59:59).
    """
    inicio_dt = datetime.combine(data_inicio, datetime.min.time())
    fim_dt = datetime.combine(data_fim, datetime.max.time())
    return inicio_dt, fim_dt


def resumo(data_inicio, data_fim):
    """
    Retorna totais gerais do período: faturamento, quantidade de
    pedidos válidos, ticket médio e quantidade de pedidos cancelados.
    """
    inicio_dt, fim_dt = _limites_datetime(data_inicio, data_fim)

    base = Order.query.filter(
        Order.created_at >= inicio_dt,
        Order.created_at <= fim_dt,
    )

    pedidos_validos = base.filter(Order.status != STATUS_CANCELADO)
    pedidos_cancelados = base.filter(Order.status == STATUS_CANCELADO)

    total_faturado = db.session.query(
        func.coalesce(func.sum(Order.total), 0)
    ).filter(
        Order.created_at >= inicio_dt,
        Order.created_at <= fim_dt,
        Order.status != STATUS_CANCELADO,
    ).scalar()

    qtd_pedidos = pedidos_validos.count()
    qtd_cancelados = pedidos_cancelados.count()

    ticket_medio = (total_faturado / qtd_pedidos) if qtd_pedidos else Decimal("0.00")

    return {
        "total_faturado": total_faturado,
        "qtd_pedidos": qtd_pedidos,
        "qtd_cancelados": qtd_cancelados,
        "ticket_medio": ticket_medio,
    }


def vendas_por_periodo(data_inicio, data_fim):
    """
    Faturamento agrupado por dia, dentro do intervalo informado.
    Ideal pra montar o relatório de vendas por período (dia/semana/mês
    é só uma questão de qual intervalo o usuário escolhe no filtro).
    """
    inicio_dt, fim_dt = _limites_datetime(data_inicio, data_fim)

    dia = func.date(Order.created_at)

    resultados = db.session.query(
        dia.label("dia"),
        func.sum(Order.total).label("total"),
        func.count(Order.id).label("qtd_pedidos"),
    ).filter(
        Order.created_at >= inicio_dt,
        Order.created_at <= fim_dt,
        Order.status != STATUS_CANCELADO,
    ).group_by(
        dia
    ).order_by(
        dia.asc()
    ).all()

    # SQLite devolve o dia como string ("2026-08-06"); Postgres pode
    # devolver como date. Normalizamos sempre para date de verdade,
    # pra quem for exibir/exportar poder formatar como dd/mm/aaaa.
    linhas = []
    for r in resultados:
        valor_dia = r.dia
        if isinstance(valor_dia, str):
            valor_dia = datetime.strptime(valor_dia, "%Y-%m-%d").date()

        linhas.append(SimpleNamespace(
            dia=valor_dia,
            total=r.total,
            qtd_pedidos=r.qtd_pedidos,
        ))

    return linhas


def produtos_mais_vendidos(data_inicio, data_fim):
    """
    Ranking de produtos por quantidade vendida e faturamento gerado,
    do maior pro menor.
    """
    inicio_dt, fim_dt = _limites_datetime(data_inicio, data_fim)

    linhas = db.session.query(
        Product.name.label("nome"),
        Product.category.label("categoria"),
        func.sum(OrderItem.quantity).label("quantidade"),
        func.sum(OrderItem.subtotal).label("total"),
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.created_at >= inicio_dt,
        Order.created_at <= fim_dt,
        Order.status != STATUS_CANCELADO,
    ).group_by(
        Product.id
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).all()

    return linhas


def vendas_por_categoria(data_inicio, data_fim):
    """
    Faturamento e quantidade vendida agrupados por categoria de produto.
    """
    inicio_dt, fim_dt = _limites_datetime(data_inicio, data_fim)

    linhas = db.session.query(
        Product.category.label("categoria"),
        func.sum(OrderItem.quantity).label("quantidade"),
        func.sum(OrderItem.subtotal).label("total"),
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.created_at >= inicio_dt,
        Order.created_at <= fim_dt,
        Order.status != STATUS_CANCELADO,
    ).group_by(
        Product.category
    ).order_by(
        func.sum(OrderItem.subtotal).desc()
    ).all()

    return linhas
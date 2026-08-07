# app/services/report_vendas_service.py

"""
Serviços responsáveis pelos relatórios de vendas.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import func

from app.models import (
    db,
    Order,
    OrderItem,
    Product,
)

STATUS_CANCELADO = "CANCELADO"


class ReportVendasService:

    @staticmethod
    def periodo_padrao():

        hoje = datetime.now(timezone.utc).date()

        inicio = hoje.replace(day=1)

        return inicio, hoje


    @staticmethod
    def _limites_datetime(data_inicio, data_fim):

        inicio_dt = datetime.combine(
            data_inicio,
            datetime.min.time()
        )

        fim_dt = datetime.combine(
            data_fim,
            datetime.max.time()
        )

        return inicio_dt, fim_dt

    @staticmethod
    def resumo(data_inicio, data_fim):
        """
        Retorna totais gerais do período:
        faturamento, quantidade de pedidos,
        ticket médio e quantidade de pedidos cancelados.
        """

        inicio_dt, fim_dt = ReportVendasService._limites_datetime(
            data_inicio,
            data_fim
        )

        base = Order.query.filter(
            Order.created_at >= inicio_dt,
            Order.created_at <= fim_dt,
        )

        pedidos_validos = base.filter(
            Order.status != STATUS_CANCELADO
        )

        pedidos_cancelados = base.filter(
            Order.status == STATUS_CANCELADO
        )

        total_faturado = db.session.query(
            func.coalesce(
                func.sum(Order.total),
                0
            )
        ).filter(
            Order.created_at >= inicio_dt,
            Order.created_at <= fim_dt,
            Order.status != STATUS_CANCELADO,
        ).scalar()

        qtd_pedidos = pedidos_validos.count()

        qtd_cancelados = pedidos_cancelados.count()

        ticket_medio = (
            total_faturado / qtd_pedidos
        ) if qtd_pedidos else Decimal("0.00")

        return {
            "total_faturado": total_faturado,
            "qtd_pedidos": qtd_pedidos,
            "qtd_cancelados": qtd_cancelados,
            "ticket_medio": ticket_medio,
        }

    @staticmethod
    def vendas_por_periodo(data_inicio, data_fim):
        """
        Retorna o faturamento agrupado por dia.
        """

        inicio_dt, fim_dt = ReportVendasService._limites_datetime(
            data_inicio,
            data_fim
        )

        dia = func.date(Order.created_at)

        resultados = db.session.query(

            dia.label("dia"),

            func.sum(Order.total).label("total"),

            func.count(Order.id).label(
                "qtd_pedidos"
            ),

        ).filter(

            Order.created_at >= inicio_dt,

            Order.created_at <= fim_dt,

            Order.status != STATUS_CANCELADO,

        ).group_by(

            dia

        ).order_by(

            dia.asc()

        ).all()

        linhas = []

        for resultado in resultados:

            valor_dia = resultado.dia

            if isinstance(valor_dia, str):

                valor_dia = datetime.strptime(
                    valor_dia,
                    "%Y-%m-%d"
                ).date()

            linhas.append(

                SimpleNamespace(

                    dia=valor_dia,

                    total=resultado.total,

                    qtd_pedidos=resultado.qtd_pedidos,

                )

            )

        return linhas


    @staticmethod
    def produtos_mais_vendidos(data_inicio, data_fim):
        """
        Ranking de produtos por quantidade vendida
        e faturamento gerado.
        """

        inicio_dt, fim_dt = ReportVendasService._limites_datetime(
            data_inicio,
            data_fim
        )

        linhas = db.session.query(

            Product.name.label(
                "nome"
            ),

            Product.category.label(
                "categoria"
            ),

            func.sum(
                OrderItem.quantity
            ).label(
                "quantidade"
            ),

            func.sum(
                OrderItem.subtotal
            ).label(
                "total"
            ),

        ).join(

            OrderItem,
            OrderItem.product_id == Product.id

        ).join(

            Order,
            Order.id == OrderItem.order_id

        ).filter(

            Order.created_at >= inicio_dt,

            Order.created_at <= fim_dt,

            Order.status != STATUS_CANCELADO,

        ).group_by(

            Product.id

        ).order_by(

            func.sum(
                OrderItem.quantity
            ).desc()

        ).all()

        return linhas

    @staticmethod
    def vendas_por_categoria(data_inicio, data_fim):
        """
        Retorna faturamento e quantidade vendida
        agrupados por categoria.
        """

        inicio_dt, fim_dt = ReportVendasService._limites_datetime(
            data_inicio,
            data_fim
        )

        linhas = db.session.query(

            Product.category.label(
                "categoria"
            ),

            func.sum(
                OrderItem.quantity
            ).label(
                "quantidade"
            ),

            func.sum(
                OrderItem.subtotal
            ).label(
                "total"
            ),

        ).join(

            OrderItem,
            OrderItem.product_id == Product.id

        ).join(

            Order,
            Order.id == OrderItem.order_id

        ).filter(

            Order.created_at >= inicio_dt,

            Order.created_at <= fim_dt,

            Order.status != STATUS_CANCELADO,

        ).group_by(

            Product.category

        ).order_by(

            func.sum(
                OrderItem.subtotal
            ).desc()

        ).all()

        return linhas
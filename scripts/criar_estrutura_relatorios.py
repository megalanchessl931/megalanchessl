#!/usr/bin/env python3
"""
Cria toda a estrutura do módulo de relatórios.

Pode ser executado várias vezes sem sobrescrever
arquivos existentes.
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "app"

# ==========================================================
# PASTAS
# ==========================================================

pastas = [
    BASE / "services",
    BASE / "templates" / "reports",
]

# ==========================================================
# SERVICES
# ==========================================================

services = [
    "report_sales_service.py",
    "report_customer_service.py",
    "report_product_service.py",
    "report_financial_service.py",
    "report_supplier_service.py",
]

# ==========================================================
# TEMPLATES
# ==========================================================

templates = [
    "dashboard.html",

    # vendas
    "vendas.html",
    "vendas_periodo.html",
    "vendas_produtos.html",
    "vendas_categoria.html",

    # clientes
    "clientes.html",
    "clientes_cadastrados.html",
    "clientes_frequentes.html",
    "clientes_ticket.html",

    # produtos
    "produtos.html",
    "produtos_mais_vendidos.html",
    "produtos_menos_vendidos.html",
    "produtos_sem_venda.html",

    # faturamento
    "faturamento.html",
    "faturamento_diario.html",
    "faturamento_mensal.html",
    "faturamento_anual.html",
    "faturamento_pagamentos.html",

    # fornecedores
    "fornecedores.html",
    "fornecedores_compras.html",
]

# ==========================================================
# CRIA PASTAS
# ==========================================================

print("\nCriando estrutura...\n")

for pasta in pastas:

    pasta.mkdir(parents=True, exist_ok=True)

    print(f"[OK] Pasta: {pasta.relative_to(BASE.parent)}")

# ==========================================================
# CRIA SERVICES
# ==========================================================

for nome in services:

    arquivo = BASE / "services" / nome

    if arquivo.exists():

        print(f"[EXISTE] {arquivo.relative_to(BASE.parent)}")

        continue

    arquivo.write_text(
        '"""\n'
        f"{nome}\n"
        '"""\n\n',
        encoding="utf-8",
    )

    print(f"[CRIADO] {arquivo.relative_to(BASE.parent)}")

# ==========================================================
# CRIA TEMPLATES
# ==========================================================

conteudo_template = """{% extends "layouts/layout_reports.html" %}

{% block title %}
Relatório
{% endblock %}

{% block content %}

<div class="card">

    <h1>Relatório</h1>

    <p>
        Em desenvolvimento.
    </p>

</div>

{% endblock %}
"""

for nome in templates:

    arquivo = BASE / "templates" / "reports" / nome

    if arquivo.exists():

        print(f"[EXISTE] {arquivo.relative_to(BASE.parent)}")

        continue

    arquivo.write_text(
        conteudo_template,
        encoding="utf-8",
    )

    print(f"[CRIADO] {arquivo.relative_to(BASE.parent)}")

print("\nEstrutura criada com sucesso.\n")
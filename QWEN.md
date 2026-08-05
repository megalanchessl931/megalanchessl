# Projeto: Mega Lanchessl

## Visão Geral
Projeto web da lanchonete "Mega Lanches" com painel administrativo integrado.
**Stack:** Python, Flask, SQLAlchemy, SQLite (desenvolvimento), PostgreSQL (produção), HTML, CSS e JavaScript.

## Estrutura do Projeto
Abaixo está o mapeamento real e atual dos diretórios e arquivos principais do projeto:

```text
/home/carlos/megalanchessl/
├── run.py                        # Arquivo de entrada principal do servidor Flask
├── QWEN.md                       # Documentação e diretrizes do projeto para a IA (este arquivo)
├── README.md                     # Documentação de instalação e configuração geral
├── requirements.txt              # Gerenciador de dependências de desenvolvimento/geral
├── requirements-prod.txt         # Gerenciador de dependências de produção
├── pytest.ini                    # Configuração para execução dos testes automatizados
├── backup.py                     # Script para backup do sistema
├── tests/                        # Pasta de testes automatizados com Pytest
│   ├── conftest.py               # Configurações e fixtures de testes do Flask/SQLAlchemy
│   ├── test_app.py               # Testes de inicialização da aplicação
│   ├── test_models.py            # Testes dos modelos de dados (User, Product, etc.)
│   ├── test_api.py               # Testes dos endpoints da API (carrinho, busca de clientes, etc.)
│   ├── test_auth.py              # Testes de autenticação e registro de usuários
│   ├── test_cart_service.py      # Testes da lógica do carrinho de compras
│   ├── test_order_service.py     # Testes da lógica de criação de pedidos
│   ├── test_orders.py            # Testes das rotas de pedidos (balcão e público)
│   ├── test_products.py          # Testes de criação e listagem de produtos
│   ├── test_public.py            # Testes das páginas públicas (index, menu, etc.)
│   └── test_security.py          # Testes de segurança e controle de acessos
├── instance/                     # Pasta com banco de dados local SQLite (app.db) e sessões
├── migrations/                   # Diretório de migrações gerenciado pelo Flask-Migrate (Alembic)
└── app/                          # Módulo principal da aplicação Flask
    ├── __init__.py               # Inicializador do Flask, registro de Blueprints e Extensões
    ├── config.py                 # Configurações do Flask e do Banco de Dados
    ├── extensions.py             # Instâncias compartilhadas das extensões do Flask (db, migrate, login, etc.)
    ├── models/                   # Modelos de banco de dados (SQLAlchemy)
    │   ├── user.py               # Modelo de Usuário administrativo/atendente
    │   ├── client.py             # Modelo de Cliente
    │   ├── product.py            # Modelo de Produto (Lanches, Bebidas, etc.)
    │   ├── order.py              # Modelo de Pedido
    │   └── order_item.py         # Modelo de itens do Pedido (relação order x product)
    ├── routes/                   # Blueprints e controladores de rota
    │   ├── admin.py              # Rotas e regras do painel administrativo
    │   ├── api.py                # Endpoints de API assíncronos (carrinho, busca de cliente)
    │   ├── auth.py               # Rotas de Login, Registro e Logout
    │   ├── orders.py             # Rotas de pedidos (balcão e público)
    │   ├── public.py             # Rotas das páginas principais (index, menu, contato)
    │   └── users.py              # Rotas para gerenciamento interno de usuários
    ├── services/                 # Lógica de negócios desacoplada das rotas
    │   ├── user_service.py       # Serviços para operações com Usuários
    │   ├── cart_service.py       # Gerenciamento do estado e regras do Carrinho
    │   ├── order_service.py      # Criação e faturamento de Pedidos
    │   ├── product_service.py    # Lógica de negócio de Produtos
    │   └── printer_service.py    # Emulação ou lógica de impressão de comandas
    ├── forms/                    # Validação de formulários usando WTForms
    │   └── user_form.py          # Formulário de criação/edição de usuários
    ├── utils/                    # Funções utilitárias auxiliares
    │   ├── csv_importer.py       # Utilitário para importar produtos do arquivo CSV
    │   └── security.py           # Decoradores e helpers de segurança de acesso
    ├── static/                   # Arquivos estáticos servidos pelo Flask
    │   ├── css/                  # Folhas de estilo (admin.css, style.css)
    │   ├── js/                   # Scripts JS (cart.js, cart_basico.js, script.js)
    │   ├── images/               # Logos, fundos e fotos dos lanches/bebidas
    │   └── fonts/                # Fontes personalizadas do projeto (ex: ahkio.ttf)
    └── templates/                # Templates HTML usando Jinja2
        ├── base.html             # Template estrutural base global
        ├── admin/                # Páginas do Painel Admin (dashboard, listas, forms de usuário, etc.)
        ├── auth/                 # Telas de Login e Registro
        ├── layouts/              # Sub-layouts específicos (layout_admin, layout_publico, etc.)
        ├── orders/               # Telas de pedidos balcão e público
        └── public/               # Páginas públicas do cardápio e contatos
```

## Regras para a IA
- Responda SEMPRE em português do Brasil.
- Antes de modificar qualquer arquivo, explique brevemente o que vai mudar.
- Faça alterações cirúrgicas; nunca reescreva arquivos inteiros sem pedir.
- Não crie arquivos novos sem confirmar antes.
- Priorize simplicidade e evite dependências externas.
- Nunca insira chaves ou segredos diretamente no código (hardcoded).
- Nunca concatene variáveis diretamente no SQL (risco de SQL Injection), use SQLAlchemy de forma segura.

## Como testar
O projeto possui uma ampla cobertura de testes com Pytest (117 testes cobrindo modelos, lógica de negócios, rotas e regras de segurança).

Para rodar os testes localmente:
```bash
# Com a venv ativa, execute o pytest no diretório raiz do projeto:
pytest
```

## Pendências / próximas tarefas
- MELHORAR OS TEMPLATES
- COLOCAR A FONTE CERTA 
- CONCLUIR O PAINEL ADMINISTRATIVO

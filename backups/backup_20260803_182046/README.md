# Mega Lanches — Módulo A

Estrutura base da migração do sistema Flask + CSV para Flask + SQLAlchemy + PostgreSQL.

## Requisitos

- Python 3.11
- PostgreSQL em produção
- SQLite em desenvolvimento
- Git
- Render para produção

## 1. Instalação local

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` e gere uma SECRET_KEY forte. Não coloque o valor no Git.

Para desenvolvimento, deixe `DATABASE_URL` vazio para usar `instance/app.db`.

## 2. Migrações

Se `migrations/` ainda não existir no projeto:

```bash
flask db init
```

Depois:

```bash
flask db migrate -m "Initial migration"
flask db upgrade
```

O `flask db init` é executado **somente uma vez**. Depois que `migrations/` existir e estiver no Git, não execute `flask db init` novamente.

## 3. Criar administrador

```bash
flask create-admin
```

O comando pede usuário, e-mail e senha no terminal. A senha é armazenada como hash bcrypt.

## 4. Importar os 38 produtos

O arquivo deve estar em:

```text
data/cardapiotrabalho.csv
```

Execute:

```bash
flask import-csv
```

Ou:

```bash
flask import-csv --file data/cardapiotrabalho.csv
```

A importação:
- converte `R$ 18,00` para Decimal;
- normaliza `xis`, `dog`, `porcao`, `porção`, `combo`, `bebida`;
- rejeita categorias desconhecidas;
- usa `placeholder.jpg` quando `foto` estiver vazia;
- atualiza o produto pelo nome se ele já existir.

## 5. Executar

```bash
flask run
```

ou:

```bash
python run.py
```

Para produção:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

A quantidade de workers deve ser ajustada ao limite de RAM do plano gratuito.

## 6. Render

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

Configure no Render as variáveis de ambiente, principalmente:

```text
SECRET_KEY
DATABASE_URL
FLASK_APP=run.py
FLASK_ENV=production
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
ALLOWED_ORIGINS=
```

O `DATABASE_URL` deve ser fornecido pelo PostgreSQL do ambiente de produção.

## 7. Segurança

Nunca faça commit do `.env`.

Antes do deploy:

```bash
bandit -r . -f html -o bandit_report.html
safety check -r requirements.txt
pip-audit
```

Execute também testes DAST em staging com OWASP ZAP antes de produção.

Verifique manualmente:
- XSS;
- SQL Injection;
- CSRF;
- autenticação;
- autorização;
- rate limiting;
- uploads, se implementados.

## 8. Imagens

Coloque o fundo atual do site em:

```text
app/static/images/fundo.jpg
```

E o placeholder em:

```text
app/static/images/placeholder.jpg
```

O fundo original não foi incluído neste pacote porque não foi enviado junto do CSV.

## 9. Regra de desenvolvimento

Não peça à IA para reescrever o projeto inteiro.

Para cada módulo:

```text
Prompt específico
→ gerar código
→ revisar manualmente
→ testar
→ commit Git
→ próximo módulo
```

Nunca aceite código que:
- contenha secrets hardcoded;
- concatene input em SQL;
- desabilite CSRF;
- permita CORS `*` sem justificativa;
- exponha stack trace em produção;
- armazene senha em texto puro.

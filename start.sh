#!/bin/bash

# Executa migrações
echo ">> Executando flask db upgrade..."
flask db upgrade

# Importa produtos do CSV
echo ">> Importando produtos do CSV..."
flask import-csv

# Cria administrador se existirem as variáveis de ambiente
if [ ! -z "$ADMIN_USERNAME" ] && [ ! -z "$ADMIN_EMAIL" ] && [ ! -z "$ADMIN_PASSWORD" ]; then
    echo ">> Criando administrador..."
    flask create-admin --username "$ADMIN_USERNAME" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
else
    echo ">> Variáveis ADMIN_USERNAME, ADMIN_EMAIL e ADMIN_PASSWORD não definidas. Pule criação de admin."
fi

# Inicia o Gunicorn
echo ">> Iniciando Gunicorn..."
exec gunicorn run:app

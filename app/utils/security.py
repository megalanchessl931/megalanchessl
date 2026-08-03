import os
import click
from getpass import getpass
from ..models import db
from ..models.user import User

def register_security_commands(app):
    @app.cli.command("create-admin")
    @click.option('--username', help='Nome de usuário')
    @click.option('--email', help='E-mail')
    @click.option('--password', help='Senha')
    def create_admin(username, email, password):
        """Cria um administrador. Pode ser usado interativamente ou com argumentos."""
        # Se todos os argumentos forem fornecidos, usa-os diretamente
        if username and email and password:
            # Validações
            if len(password) < 8:
                click.echo("Erro: A senha deve ter pelo menos 8 caracteres.")
                return
            # Verifica se já existe
            if User.query.filter((User.username == username) | (User.email == email)).first():
                click.echo(f"Erro: Usuário '{username}' ou e-mail '{email}' já cadastrado.")
                return
            user = User(username=username, email=email, is_admin=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f"Administrador '{username}' criado com sucesso.")
            return

        # Modo interativo (se os argumentos não foram fornecidos)
        username = click.prompt("Usuário", type=str).strip()
        email = click.prompt("E-mail", type=str).strip().lower()
        password = getpass("Senha: ")
        confirm = getpass("Confirme a senha: ")

        if not password or len(password) < 8:
            raise click.ClickException("A senha deve ter pelo menos 8 caracteres.")
        if password != confirm:
            raise click.ClickException("As senhas não coincidem.")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            raise click.ClickException("Usuário ou e-mail já cadastrado.")

        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrador criado com sucesso.")

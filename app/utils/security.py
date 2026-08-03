import os
import click
from getpass import getpass
from ..models import db
from ..models.user import User

def register_security_commands(app):
    @app.cli.command("create-admin")
    def create_admin():
        """Cria um administrador solicitando credenciais no terminal."""
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

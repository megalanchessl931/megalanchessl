# app/services/user_service.py

from app.models import db
from app.models.user import User


class UserService:
    """
    Serviço responsável por todas as operações relacionadas
    aos usuários do sistema.
    """

    @staticmethod
    def list_all():
        """
        Retorna todos os usuários ordenados pelo nome.
        """
        return (
            User.query
            .order_by(User.username.asc())
            .all()
        )

    @staticmethod
    def get(user_id):
        """
        Busca um usuário pelo ID.
        """
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username):
        """
        Busca um usuário pelo nome.
        """
        username = username.strip()

        return User.query.filter_by(
            username=username
        ).first()

    @staticmethod
    def get_by_email(email):
        """
        Busca um usuário pelo e-mail.
        """
        email = email.strip().lower()

        return User.query.filter_by(
            email=email
        ).first()

    @staticmethod
    def create_user(
        username,
        email,
        password,
        is_admin=False,
        is_active=True
    ):
        """
        Cria um novo usuário.
        """

        username = username.strip()
        email = email.strip().lower()

        if UserService.get_by_username(username):
            raise ValueError(
                "Nome de usuário já cadastrado."
            )

        if UserService.get_by_email(email):
            raise ValueError(
                "E-mail já cadastrado."
            )

        user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            is_active=is_active
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def update_user(
        user,
        username,
        email,
        is_admin,
        is_active
    ):
        """
        Atualiza os dados de um usuário.
        """

        username = username.strip()
        email = email.strip().lower()

        if not username:
            raise ValueError(
                "Informe o nome do usuário."
            )

        if not email:
            raise ValueError(
                "Informe o e-mail."
            )

        outro = (
            User.query
            .filter(
                User.username == username,
                User.id != user.id
            )
            .first()
        )

        if outro:
            raise ValueError(
                "Nome de usuário já utilizado."
            )

        outro = (
            User.query
            .filter(
                User.email == email,
                User.id != user.id
            )
            .first()
        )

        if outro:
            raise ValueError(
                "E-mail já utilizado."
            )

        user.username = username
        user.email = email
        user.is_admin = is_admin
        user.is_active = is_active

        db.session.commit()

        return user
    
    @staticmethod
    def change_password(user, password):
        """
        Atualiza a senha do usuário.
        """

        if not password:
            return user

        user.set_password(password)

        db.session.commit()

        return user

    @staticmethod
    def activate(user):
        """
        Ativa um usuário.
        """

        user.is_active = True

        db.session.commit()

        return user

    @staticmethod
    def deactivate(user):
        """
        Desativa um usuário.
        """

        if user.is_admin:

            admins_ativos = (
                User.query
                .filter_by(
                    is_admin=True,
                    is_active=True
                )
                .count()
            )

            if admins_ativos <= 1:
                raise ValueError(
                    "O último administrador ativo não pode ser desativado."
                )

        user.is_active = False

        db.session.commit()

        return user

    @staticmethod
    def delete(user):
        """
        Remove um usuário.
        """

        if user.is_admin:
            raise ValueError(
                "Administradores não podem ser excluídos."
            )

        db.session.delete(user)

        db.session.commit()

        return True

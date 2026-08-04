from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Optional
)


class UserForm(FlaskForm):

    username = StringField(
        "Usuário",
        validators=[
            DataRequired(),
            Length(min=3, max=50)
        ]
    )

    email = StringField(
        "E-mail",
        validators=[
            DataRequired(),
            Email(),
            Length(max=100)
        ]
    )

    password = PasswordField(
        "Senha",
        validators=[
            Optional(),
            Length(min=6)
        ]
    )

    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[
            Optional(),
            EqualTo(
                "password",
                message="As senhas não conferem."
            )
        ]
    )
    
    is_admin = BooleanField(
        "Administrador"
    )

    is_active = BooleanField(
        "Usuário ativo",
        default=True
    )

    submit = SubmitField(
        "Salvar"
    )

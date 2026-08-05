from flask_wtf import FlaskForm

from wtforms import (
    SelectField,
    DecimalField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Optional
)


class PriceUpdateForm(FlaskForm):

    # Escopo do reajuste: todos os produtos ou apenas um produto específico.
    # As opções de "product_id" são preenchidas dinamicamente na rota,
    # já que dependem dos produtos cadastrados no banco.
    scope = SelectField(
        "Aplicar em",
        choices=[
            ("all", "Todos os produtos"),
            ("single", "Um produto específico"),
        ],
        validators=[
            DataRequired()
        ]
    )

    product_id = SelectField(
        "Produto",
        choices=[],
        validators=[
            Optional()
        ]
    )

    mode = SelectField(
        "Tipo de reajuste",
        choices=[
            ("percent", "Percentual (%)"),
            ("fixed", "Valor fixo (R$)"),
        ],
        validators=[
            DataRequired()
        ]
    )

    # Aceita valores negativos (para reduzir preços), positivos para aumentar
    value = DecimalField(
        "Valor do reajuste",
        places=2,
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField(
        "Aplicar reajuste"
    )

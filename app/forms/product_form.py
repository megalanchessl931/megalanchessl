from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed

from wtforms import (
    StringField,
    TextAreaField,
    DecimalField,
    IntegerField,
    SelectField,
    BooleanField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional
)

# Categorias fixas do cardápio (definidas junto com Carlos)
CATEGORIAS_PRODUTO = [
    ("XIS", "XIS"),
    ("DOG", "DOG"),
    ("BEBIDAS", "BEBIDAS"),
    ("PORÇÃO", "PORÇÃO"),
    ("COMBOS", "COMBOS"),
    ("COMPLEMENTOS", "COMPLEMENTOS"),
]

# Extensões de imagem aceitas no upload
EXTENSOES_IMAGEM_PERMITIDAS = ["jpg", "jpeg", "png", "webp"]


class ProductForm(FlaskForm):

    name = StringField(
        "Nome do produto",
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )

    description = TextAreaField(
        "Descrição",
        validators=[
            Optional(),
            Length(max=2000)
        ]
    )

    price = DecimalField(
        "Preço (R$)",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0, message="O preço não pode ser negativo.")
        ]
    )

    category = SelectField(
        "Categoria",
        choices=CATEGORIAS_PRODUTO,
        validators=[
            DataRequired()
        ]
    )

    image = FileField(
        "Imagem do produto",
        validators=[
            Optional(),
            FileAllowed(
                EXTENSOES_IMAGEM_PERMITIDAS,
                "Envie uma imagem nos formatos: jpg, jpeg, png ou webp."
            )
        ]
    )

    order = IntegerField(
        "Ordem de exibição",
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0)
        ]
    )

    is_active = BooleanField(
        "Produto ativo",
        default=True
    )

    submit = SubmitField(
        "Salvar"
    )
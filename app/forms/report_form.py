from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField
from wtforms.validators import Optional


class ReportFilterForm(FlaskForm):
    """
    Formulário simples de filtro de período (de/até) usado em todos
    os relatórios. Os dois campos são opcionais — se vazios, a rota
    aplica um período padrão (mês atual).
    """

    data_inicio = DateField(
        "De",
        validators=[Optional()],
        format="%Y-%m-%d"
    )

    data_fim = DateField(
        "Até",
        validators=[Optional()],
        format="%Y-%m-%d"
    )

    submit = SubmitField("Filtrar")
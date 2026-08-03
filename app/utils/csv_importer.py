import csv
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
import unicodedata
import click
from flask import current_app

from ..models import db
from ..models.product import Product

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "xis": "XIS",
    "dog": "DOG",
    "porcao": "PORCAO",
    "porção": "PORCAO",
    "combo": "COMBO",
    "bebida": "BEBIDA",
}

def normalize_category(value):
    raw = (value or "").strip().lower()
    normalized = unicodedata.normalize("NFKC", raw)
    return CATEGORY_MAP.get(normalized)

def parse_price(value):
    raw = (value or "").strip()
    raw = raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Preço inválido: {value!r}")

def register_import_command(app):
    @app.cli.command("import-csv")
    @click.option("--file", "csv_file", default="data/cardapiotrabalho.csv", show_default=True)
    def import_csv(csv_file):
        """Importa/atualiza produtos do CSV do cardápio."""
        path = Path(csv_file)
        if not path.is_absolute():
            path = Path(current_app.root_path).parent / path

        if not path.exists():
            raise click.ClickException(f"Arquivo não encontrado: {path}")

        inserted = updated = rejected = 0

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"produto", "preco", "descricao", "foto", "tipo", "tipoproducao"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise click.ClickException(
                    f"Colunas inválidas. Esperadas: {sorted(required)}"
                )

            for line_number, row in enumerate(reader, start=2):
                name = (row.get("produto") or "").strip()
                category = normalize_category(row.get("tipoproducao"))

                if not name:
                    logger.error("Linha %s rejeitada: produto vazio.", line_number)
                    rejected += 1
                    continue

                if not category:
                    logger.error(
                        "Linha %s rejeitada: categoria desconhecida: %r",
                        line_number,
                        row.get("tipoproducao"),
                    )
                    rejected += 1
                    continue

                try:
                    price = parse_price(row.get("preco"))
                except ValueError as exc:
                    logger.error("Linha %s rejeitada: %s", line_number, exc)
                    rejected += 1
                    continue

                image = (row.get("foto") or "").strip() or "placeholder.jpg"

                product = Product.query.filter_by(name=name).first()
                if product is None:
                    product = Product(name=name)
                    db.session.add(product)
                    inserted += 1
                else:
                    updated += 1

                product.description = (row.get("descricao") or "").strip()
                product.price = price
                product.image_filename = image
                product.category = category
                product.is_active = True

        db.session.commit()
        click.echo(
            f"Importação concluída: {inserted} inseridos, "
            f"{updated} atualizados, {rejected} rejeitados."
        )

# app/forms/__init__.py

from .user_form import UserForm
from .product_form import ProductForm, CATEGORIAS_PRODUTO
from .price_update_form import PriceUpdateForm

__all__ = [
    "UserForm",
    "ProductForm",
    "CATEGORIAS_PRODUTO",
    "PriceUpdateForm",
]

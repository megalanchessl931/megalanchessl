# app/models/__init__.py

from ..extensions import db
from .user import User
from .product import Product
from .client import Client
from .order import Order
from .order_item import OrderItem

__all__ = ["db", "User", "Product", "Client", "Order", "OrderItem"]

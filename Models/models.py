"""Compatibilidade com imports antigos; os modelos vivem em models.py."""

from models import ItensPedido, Pedido, Pizza, Usuario
from database import Base, db

__all__ = ["Base", "db", "Usuario", "Pedido", "Pizza", "ItensPedido"]

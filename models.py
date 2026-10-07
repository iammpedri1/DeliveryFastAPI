from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column("senha", String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pedidos: Mapped[list["Pedido"]] = relationship("Pedido", back_populates="usuario_obj")
    notificacoes: Mapped[list["Notificacao"]] = relationship("Notificacao", back_populates="usuario_obj")


class Pedido(Base):
    __tablename__ = "pedidos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDENTE", nullable=False)
    usuario: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    preco: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    usuario_obj: Mapped["Usuario"] = relationship("Usuario", back_populates="pedidos")
    itens: Mapped[list["ItensPedido"]] = relationship(
        "ItensPedido", cascade="all, delete-orphan", back_populates="pedido_obj"
    )
    notificacoes: Mapped[list["Notificacao"]] = relationship("Notificacao", back_populates="pedido_obj")

    def calcular_preco(self) -> float:
        return sum(item.quantidade * item.preco_unitario for item in self.itens)


class Pizza(Base):
    __tablename__ = "pizzas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sabor: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    preco: Mapped[float] = mapped_column(Float, nullable=False)
    preco_pequeno: Mapped[float | None] = mapped_column(Float)
    preco_grande: Mapped[float | None] = mapped_column(Float)

    @property
    def preco_medio(self) -> float:
        return self.preco


class ItensPedido(Base):
    __tablename__ = "itens_pedido"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    sabor: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho: Mapped[str] = mapped_column(String(20), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    pedido: Mapped[int] = mapped_column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    pedido_obj: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")


class Notificacao(Base):
    __tablename__ = "notificacoes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    pedido: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"), nullable=True, index=True)
    mensagem: Mapped[str] = mapped_column(String(240), nullable=False)
    lida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario_obj: Mapped["Usuario"] = relationship("Usuario", back_populates="notificacoes")
    pedido_obj: Mapped["Pedido | None"] = relationship("Pedido", back_populates="notificacoes")

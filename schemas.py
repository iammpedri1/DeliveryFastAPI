from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

TamanhoPizza = Literal["PEQUENO", "MEDIO", "GRANDE"]
StatusPedido = Literal["PENDENTE", "EM_PREPARO", "SAIU_PARA_ENTREGA", "FINALIZADO", "CANCELADO"]


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    ativo: bool
    admin: bool
    model_config = ConfigDict(from_attributes=True)


class LoginSchema(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class PedidoResponse(BaseModel):
    id: int
    status: str
    usuario: int
    preco: float
    model_config = ConfigDict(from_attributes=True)


class ItemPedidoCreate(BaseModel):
    quantidade: int = Field(gt=0, le=50)
    sabor: str = Field(min_length=2, max_length=100)
    tamanho: TamanhoPizza


class CheckoutCreate(BaseModel):
    itens: list[ItemPedidoCreate] = Field(min_length=1, max_length=30)


class ItemPedidoResponse(BaseModel):
    id: int
    quantidade: int
    sabor: str
    tamanho: str
    preco_unitario: float
    pedido: int
    model_config = ConfigDict(from_attributes=True)


class PedidoDetalheResponse(PedidoResponse):
    itens: list[ItemPedidoResponse]


class StatusPedidoUpdate(BaseModel):
    status: StatusPedido


class NotificacaoResponse(BaseModel):
    id: int
    pedido: int | None
    mensagem: str
    lida: bool
    criada_em: datetime
    model_config = ConfigDict(from_attributes=True)


class PizzaCreate(BaseModel):
    sabor: str = Field(min_length=2, max_length=100)
    preco_pequeno: float = Field(gt=0)
    preco_medio: float = Field(gt=0)
    preco_grande: float = Field(gt=0)


class PizzaUpdate(BaseModel):
    sabor: str | None = Field(default=None, min_length=2, max_length=100)
    preco_pequeno: float | None = Field(default=None, gt=0)
    preco_medio: float | None = Field(default=None, gt=0)
    preco_grande: float | None = Field(default=None, gt=0)


class PizzaResponse(BaseModel):
    id: int
    sabor: str
    preco_pequeno: float
    preco_medio: float
    preco_grande: float
    model_config = ConfigDict(from_attributes=True)

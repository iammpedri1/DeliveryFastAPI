from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencies import AdminUser, CurrentUser, DbSession
from models import ItensPedido, Notificacao, Pizza, Pedido, Usuario
from schemas import CheckoutCreate, ItemPedidoCreate, ItemPedidoResponse, PedidoDetalheResponse, PedidoResponse, StatusPedidoUpdate
order_router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def buscar_pedido_acessivel(id_pedido: int, session: Session, usuario: Usuario):
    stmt = select(Pedido).where(Pedido.id == id_pedido)
    if not usuario.admin:
        stmt = stmt.where(Pedido.usuario == usuario.id)
    return session.scalar(stmt)


@order_router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(session: DbSession, usuario: CurrentUser):
    pedido = Pedido(status="PENDENTE", usuario=usuario.id, preco=0)
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


@order_router.post("/checkout", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def finalizar_compra(data: CheckoutCreate, session: DbSession, usuario: CurrentUser):
    sabores = {item.sabor for item in data.itens}
    pizzas = {
        pizza.sabor: pizza
        for pizza in session.scalars(select(Pizza).where(Pizza.sabor.in_(sabores))).all()
    }
    if sabores - pizzas.keys():
        raise HTTPException(status_code=404, detail="Pizza não encontrada no cardápio")

    pedido = Pedido(status="PENDENTE", usuario=usuario.id, preco=0)
    for dado in data.itens:
        pizza = pizzas[dado.sabor]
        preco = {"PEQUENO": pizza.preco_pequeno, "MEDIO": pizza.preco_medio, "GRANDE": pizza.preco_grande}[dado.tamanho]
        pedido.itens.append(
            ItensPedido(
                quantidade=dado.quantidade,
                sabor=pizza.sabor,
                tamanho=dado.tamanho,
                preco_unitario=preco,
            )
        )
    pedido.preco = pedido.calcular_preco()
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


@order_router.get("/", response_model=list[PedidoResponse])
def listar_pedidos(session: DbSession, usuario: CurrentUser):
    stmt = select(Pedido).order_by(Pedido.id.desc())
    if not usuario.admin:
        stmt = stmt.where(Pedido.usuario == usuario.id)
    return list(session.scalars(stmt).all())


@order_router.get("/{id_pedido}", response_model=PedidoDetalheResponse)
def get_pedido(id_pedido: int, session: DbSession, usuario: CurrentUser):
    pedido = buscar_pedido_acessivel(id_pedido, session, usuario)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


@order_router.post("/{id_pedido}/itens", response_model=ItemPedidoResponse, status_code=status.HTTP_201_CREATED)
def adicionar_item_pedido(id_pedido: int, data: ItemPedidoCreate, session: DbSession, usuario: CurrentUser):
    pedido = buscar_pedido_acessivel(id_pedido, session, usuario)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status != "PENDENTE":
        raise HTTPException(status_code=409, detail="O pedido não pode mais receber itens")
    pizza = session.scalar(select(Pizza).where(Pizza.sabor == data.sabor))
    if pizza is None:
        raise HTTPException(status_code=404, detail="Pizza não encontrada no cardápio")
    preco = {"PEQUENO": pizza.preco_pequeno, "MEDIO": pizza.preco_medio, "GRANDE": pizza.preco_grande}[data.tamanho]
    item = ItensPedido(
        quantidade=data.quantidade,
        sabor=pizza.sabor,
        tamanho=data.tamanho,
        preco_unitario=preco,
    )
    pedido.itens.append(item)
    session.flush()
    pedido.preco = pedido.calcular_preco()
    session.commit()
    session.refresh(item)
    return item


@order_router.patch("/{id_pedido}/status", response_model=PedidoResponse)
def alterar_status_pedido(id_pedido: int, data: StatusPedidoUpdate, session: DbSession, usuario: AdminUser):
    pedido = session.scalar(select(Pedido).where(Pedido.id == id_pedido))
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status == data.status:
        return pedido
    pedido.status = data.status
    mensagens = {
        "PENDENTE": "foi recebido e aguarda confirmação",
        "EM_PREPARO": "entrou em preparo",
        "SAIU_PARA_ENTREGA": "saiu para entrega",
        "FINALIZADO": "foi finalizado",
        "CANCELADO": "foi cancelado pelo restaurante",
    }
    session.add(Notificacao(usuario=pedido.usuario, pedido=pedido.id, mensagem=f"Pedido #{pedido.id} {mensagens[data.status]}"))
    session.commit()
    session.refresh(pedido)
    return pedido


@order_router.post("/{id_pedido}/cancelar", response_model=PedidoResponse)
def cancelar_pedido(id_pedido: int, session: DbSession, usuario: CurrentUser):
    pedido = session.scalar(
        select(Pedido).where(Pedido.id == id_pedido, Pedido.usuario == usuario.id)
    )
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status != "PENDENTE":
        raise HTTPException(status_code=409, detail="Só é possível cancelar pedidos pendentes")
    pedido.status = "CANCELADO"
    session.add(Notificacao(usuario=usuario.id, pedido=pedido.id, mensagem=f"Pedido #{pedido.id} foi cancelado por você"))
    session.commit()
    session.refresh(pedido)
    return pedido

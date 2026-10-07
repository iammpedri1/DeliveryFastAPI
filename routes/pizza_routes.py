from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from dependencies import AdminUser, DbSession
from models import Pizza
from schemas import PizzaCreate, PizzaResponse, PizzaUpdate

pizza_router = APIRouter(prefix="/pizzas", tags=["pizzas"])
admin_pizza_router = APIRouter(prefix="/admin/pizzas", tags=["admin"])


@pizza_router.get("/", response_model=list[PizzaResponse])
def listar_pizzas(session: DbSession):
    return list(session.scalars(select(Pizza).order_by(Pizza.sabor)).all())


@admin_pizza_router.post("/", response_model=PizzaResponse, status_code=status.HTTP_201_CREATED)
def criar_pizza(data: PizzaCreate, session: DbSession, usuario: AdminUser):
    sabor = data.sabor.strip()
    if session.scalar(select(Pizza).where(Pizza.sabor == sabor)):
        raise HTTPException(status_code=409, detail="Pizza já cadastrada")
    pizza = Pizza(
        sabor=sabor,
        preco=data.preco_medio,
        preco_pequeno=data.preco_pequeno,
        preco_grande=data.preco_grande,
    )
    session.add(pizza)
    session.commit()
    session.refresh(pizza)
    return pizza


@admin_pizza_router.patch("/{id_pizza}", response_model=PizzaResponse)
def atualizar_pizza(id_pizza: int, data: PizzaUpdate, session: DbSession, usuario: AdminUser):
    pizza = session.scalar(select(Pizza).where(Pizza.id == id_pizza))
    if pizza is None:
        raise HTTPException(status_code=404, detail="Pizza não encontrada")
    changes = data.model_dump(exclude_unset=True)
    if "sabor" in changes:
        changes["sabor"] = changes["sabor"].strip()
    for field, value in changes.items():
        setattr(pizza, "preco" if field == "preco_medio" else field, value)
    session.commit()
    session.refresh(pizza)
    return pizza

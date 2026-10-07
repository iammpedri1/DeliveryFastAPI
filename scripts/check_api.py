"""Business-flow checks on an isolated SQLite database, without network access."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import Base, db, engine as configured_engine
from dependencies import get_current_user, require_admin
from models import Notificacao, Pedido, Pizza, Usuario
from routes.auth_routes import signin, signup
from routes.notification_routes import listar_notificacoes, marcar_como_lida
from routes.order_routes import (
    adicionar_item_pedido, alterar_status_pedido, buscar_pedido_acessivel, finalizar_compra,
    cancelar_pedido, criar_pedido, get_pedido, listar_pedidos,
)
from routes.pizza_routes import criar_pizza
from schemas import (
    CheckoutCreate, ItemPedidoCreate, LoginSchema, NotificacaoResponse, PedidoDetalheResponse,
    PizzaCreate, PizzaResponse, StatusPedidoUpdate, UsuarioCreate,
)


def expect_http_error(status_code, function, *args):
    try:
        function(*args)
    except HTTPException as error:
        assert error.status_code == status_code, (error.status_code, status_code)
    else:
        raise AssertionError(f"Expected HTTP {status_code} from {function.__name__}")


async def check_app_startup():
    async with main.app.router.lifespan_context(main.app):
        assert len(main.app.openapi()["paths"]) >= 13


def run():
    assert db is configured_engine  # Compatibility for existing `from database import db` imports.
    asyncio.run(check_app_startup())
    fresh_engine = create_engine("sqlite://")
    main.inicializar_banco(fresh_engine)
    with sessionmaker(bind=fresh_engine)() as session:
        seeded = session.scalars(select(Pizza).order_by(Pizza.id)).all()
        assert len(seeded) == 4 and all(pizza.preco_pequeno < pizza.preco_medio < pizza.preco_grande for pizza in seeded)

    legacy_engine = create_engine("sqlite://")
    with legacy_engine.begin() as connection:
        connection.execute(text("CREATE TABLE pizzas (id INTEGER PRIMARY KEY, sabor VARCHAR(100), preco FLOAT)"))
        connection.execute(text("INSERT INTO pizzas (sabor, preco) VALUES ('Legacy', 25)"))
    Base.metadata.create_all(legacy_engine)
    main.migrar_precos_por_tamanho(legacy_engine)
    with legacy_engine.connect() as connection:
        prices = connection.execute(text("SELECT preco_pequeno, preco, preco_grande FROM pizzas WHERE sabor='Legacy'")).one()
        assert prices == (20, 25, 35)

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionTest = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionTest() as session:
        ana = signup(UsuarioCreate(nome="Ana Teste", email="ana@example.com", senha="SenhaTeste123"), session)
        bia = signup(UsuarioCreate(nome="Bia Teste", email="bia@example.com", senha="SenhaTeste123"), session)
        admin = signup(UsuarioCreate(nome="Admin Teste", email="admin@example.com", senha="SenhaTeste123"), session)
        assert session.scalar(select(Pedido)) is None  # Signup never creates an order.
        assert not ana.admin and not bia.admin and not admin.admin  # Public signup never grants admin access.
        expect_http_error(409, signup, UsuarioCreate(nome="Ana duplicada", email="ana@example.com", senha="SenhaTeste123"), session)
        expect_http_error(401, signin, LoginSchema(email="ana@example.com", senha="senha errada"), session)
        token_ana = signin(LoginSchema(email="ana@example.com", senha="SenhaTeste123"), session).access_token
        token_bia = signin(LoginSchema(email="bia@example.com", senha="SenhaTeste123"), session).access_token
        admin.admin = True
        session.commit()
        token_admin = signin(LoginSchema(email="admin@example.com", senha="SenhaTeste123"), session).access_token
        expect_http_error(401, get_current_user, None, session)
        user_ana = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_ana), session)
        user_bia = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_bia), session)
        user_admin = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_admin), session)
        assert user_ana.id == ana.id and not user_ana.admin
        expect_http_error(403, require_admin, user_ana)

        pizza = Pizza(sabor="Pizza teste", preco=20, preco_pequeno=15, preco_grande=28)
        session.add(pizza)
        session.commit()
        order = criar_pedido(session, user_ana)
        tampered = ItemPedidoCreate.model_validate({"quantidade": 2, "sabor": "Pizza teste", "tamanho": "GRANDE", "preco_unitario": 0.01})
        item = adicionar_item_pedido(order.id, tampered, session, user_ana)
        assert item.preco_unitario == 28 and session.get(Pedido, order.id).preco == 56
        assert PedidoDetalheResponse.model_validate(session.get(Pedido, order.id)).preco == 56
        small = adicionar_item_pedido(order.id, ItemPedidoCreate(quantidade=1, sabor="Pizza teste", tamanho="PEQUENO"), session, user_ana)
        medium = adicionar_item_pedido(order.id, ItemPedidoCreate(quantidade=1, sabor="Pizza teste", tamanho="MEDIO"), session, user_ana)
        assert (small.preco_unitario, medium.preco_unitario) == (15, 20)
        assert session.get(Pedido, order.id).preco == 91
        assert [p.id for p in listar_pedidos(session, user_bia)] == []
        assert buscar_pedido_acessivel(order.id, session, user_bia) is None
        expect_http_error(404, get_pedido, order.id, session, user_bia)
        expect_http_error(404, adicionar_item_pedido, order.id, ItemPedidoCreate(quantidade=1, sabor="Pizza teste", tamanho="PEQUENO"), session, user_bia)
        try:
            ItemPedidoCreate(quantidade=0, sabor="Pizza teste", tamanho="GRANDE")
        except ValidationError:
            pass
        else:
            raise AssertionError("Zero-quantity items must fail schema validation")

        order_count_before_checkout = session.query(Pedido).count()
        checkout = finalizar_compra(
            CheckoutCreate(itens=[ItemPedidoCreate(quantidade=2, sabor="Pizza teste", tamanho="PEQUENO")]),
            session,
            user_ana,
        )
        assert checkout.usuario == ana.id and checkout.preco == 30
        assert session.query(Pedido).count() == order_count_before_checkout + 1
        expect_http_error(
            404,
            finalizar_compra,
            CheckoutCreate(itens=[ItemPedidoCreate(quantidade=1, sabor="Sabor inexistente", tamanho="GRANDE")]),
            session,
            user_ana,
        )
        assert session.query(Pedido).count() == order_count_before_checkout + 1

        created_pizza = criar_pizza(PizzaCreate(sabor="Pizza admin", preco_pequeno=10, preco_medio=14, preco_grande=18), session, user_admin)
        assert (created_pizza.preco_pequeno, created_pizza.preco_medio, created_pizza.preco_grande) == (10, 14, 18)
        assert PizzaResponse.model_validate(created_pizza).preco_grande == 18
        assert len(listar_pedidos(session, user_admin)) == session.query(Pedido).count()
        altered = alterar_status_pedido(order.id, StatusPedidoUpdate(status="SAIU_PARA_ENTREGA"), session, user_admin)
        assert altered.status == "SAIU_PARA_ENTREGA"
        notes = listar_notificacoes(session, user_ana)
        assert len(notes) == 1 and "saiu para entrega" in notes[0].mensagem
        assert NotificacaoResponse.model_validate(notes[0]).pedido == order.id
        expect_http_error(404, marcar_como_lida, notes[0].id, session, user_bia)
        marcar_como_lida(notes[0].id, session, user_ana)
        assert notes[0].lida
        altered_again = alterar_status_pedido(order.id, StatusPedidoUpdate(status="SAIU_PARA_ENTREGA"), session, user_admin)
        assert altered_again.id == order.id and len(listar_notificacoes(session, user_ana)) == 1
        expect_http_error(409, adicionar_item_pedido, order.id, ItemPedidoCreate(quantidade=1, sabor="Pizza teste", tamanho="PEQUENO"), session, user_ana)

        pending = criar_pedido(session, user_ana)
        canceled = cancelar_pedido(pending.id, session, user_ana)
        assert canceled.status == "CANCELADO"
        assert "cancelado por você" in listar_notificacoes(session, user_ana)[0].mensagem
        expect_http_error(409, cancelar_pedido, pending.id, session, user_ana)
        expect_http_error(404, cancelar_pedido, pending.id, session, user_bia)
        assert listar_notificacoes(session, user_bia) == []

        admin.ativo = False
        session.commit()
        expect_http_error(401, get_current_user, HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_admin), session)
        expect_http_error(403, signin, LoginSchema(email="admin@example.com", senha="SenhaTeste123"), session)
        expect_http_error(401, get_current_user, HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token"), session)
        assert session.scalar(select(Notificacao).where(Notificacao.usuario == ana.id)) is not None

    print("Checks passed: app imports, signup has no order, auth/roles, size pricing, ownership, cancellation, status changes, and private notifications.")


if __name__ == "__main__":
    run()

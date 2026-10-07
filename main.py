import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

from database import Base, db
from models import ItensPedido, Notificacao, Pedido, Pizza, Usuario  # noqa: F401
from routes.auth_routes import auth_router
from routes.order_routes import order_router
from routes.pizza_routes import admin_pizza_router, pizza_router
from routes.notification_routes import notification_router


def migrar_precos_por_tamanho(engine):
    with engine.begin() as connection:
        columns = {
            column["name"] for column in inspect(connection).get_columns("pizzas")
        }
        if "preco_pequeno" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE pizzas ADD COLUMN preco_pequeno FLOAT"
            )
        if "preco_grande" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE pizzas ADD COLUMN preco_grande FLOAT"
            )
        connection.execute(
            text(
                "UPDATE pizzas SET preco_pequeno = preco * 0.8 WHERE preco_pequeno IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE pizzas SET preco_grande = preco * 1.4 WHERE preco_grande IS NULL"
            )
        )


def inicializar_banco(engine=db):
    Base.metadata.create_all(bind=engine)
    migrar_precos_por_tamanho(engine)
    with sessionmaker(bind=engine)() as session:
        if session.query(Pizza).count() == 0:
            session.add_all(
                [
                    Pizza(
                        sabor="Margherita",
                        preco_pequeno=31.90,
                        preco=39.90,
                        preco_grande=49.90,
                    ),
                    Pizza(
                        sabor="Calabresa",
                        preco_pequeno=35.90,
                        preco=44.90,
                        preco_grande=55.90,
                    ),
                    Pizza(
                        sabor="Quatro Queijos",
                        preco_pequeno=39.90,
                        preco=49.90,
                        preco_grande=61.90,
                    ),
                    Pizza(
                        sabor="Portuguesa",
                        preco_pequeno=37.90,
                        preco=47.90,
                        preco_grande=59.90,
                    ),
                ]
            )
            session.commit()


@asynccontextmanager
async def lifespan(app):
    inicializar_banco()
    yield


app = FastAPI(title="Delivery API", version="2.0.0", lifespan=lifespan)
origins = [
    item.strip()
    for item in os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(pizza_router)
app.include_router(admin_pizza_router)
app.include_router(notification_router)
app.mount(
    "/site",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="site",
)


@app.get("/", tags=["home"])
def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

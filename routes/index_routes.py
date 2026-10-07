from fastapi import APIRouter

index_router = APIRouter(prefix="", tags=["Home"])


@index_router.get("/")
async def root():
    return {"message": "Bem-vindo à API de Delivery! Acesse /docs para a documentação."}

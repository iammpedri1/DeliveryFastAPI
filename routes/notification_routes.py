from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from dependencies import CurrentUser, DbSession
from models import Notificacao
from schemas import NotificacaoResponse

notification_router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


@notification_router.get("/", response_model=list[NotificacaoResponse])
def listar_notificacoes(session: DbSession, usuario: CurrentUser):
    return list(session.scalars(
        select(Notificacao).where(Notificacao.usuario == usuario.id).order_by(Notificacao.id.desc())
    ).all())


@notification_router.patch("/{id_notificacao}/lida", response_model=NotificacaoResponse)
def marcar_como_lida(id_notificacao: int, session: DbSession, usuario: CurrentUser):
    notificacao = session.scalar(
        select(Notificacao).where(Notificacao.id == id_notificacao, Notificacao.usuario == usuario.id)
    )
    if notificacao is None:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    notificacao.lida = True
    session.commit()
    session.refresh(notificacao)
    return notificacao

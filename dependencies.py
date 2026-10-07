from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Usuario
from security import ALGORITHM, SECRET_KEY

bearer_scheme = HTTPBearer(auto_error=False)


def pegar_sessao():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(pegar_sessao)],
) -> Usuario:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise auth_error
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if payload.get("type") != "access" or not isinstance(user_id, str):
            raise auth_error
        user_id = int(user_id)
    except (InvalidTokenError, TypeError, ValueError):
        raise auth_error
    usuario = session.scalar(select(Usuario).where(Usuario.id == user_id))
    if usuario is None or not usuario.ativo:
        raise auth_error
    return usuario


def require_admin(usuario: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
    if not usuario.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores")
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]
AdminUser = Annotated[Usuario, Depends(require_admin)]
DbSession = Annotated[Session, Depends(pegar_sessao)]

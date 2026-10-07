import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if APP_ENV == "production":
        raise RuntimeError("Configure uma SECRET_KEY aleatória com pelo menos 32 caracteres.")
    SECRET_KEY = secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def criar_hash(senha: str) -> str:
    return password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return password_hash.verify(senha, senha_hash)


def criar_token_acesso(user_id: int) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": agora, "exp": agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "type": "access"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

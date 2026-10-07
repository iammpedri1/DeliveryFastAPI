from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from dependencies import CurrentUser, DbSession
from models import Usuario
from schemas import LoginSchema, TokenResponse, UsuarioCreate, UsuarioResponse
from security import criar_hash, criar_token_acesso, verificar_senha

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def signup(data: UsuarioCreate, session: DbSession):
    email = str(data.email).strip().lower()
    if session.scalar(select(Usuario).where(Usuario.email == email)):
        raise HTTPException(status_code=409, detail="Email já cadastrado")
    usuario = Usuario(nome=data.nome.strip(), email=email, senha_hash=criar_hash(data.senha), ativo=True, admin=False)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@auth_router.post("/signin", response_model=TokenResponse)
def signin(data: LoginSchema, session: DbSession):
    email = str(data.email).strip().lower()
    usuario = session.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is None or not verificar_senha(data.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos", headers={"WWW-Authenticate": "Bearer"})
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    return TokenResponse(access_token=criar_token_acesso(usuario.id))


@auth_router.get("/me", response_model=UsuarioResponse)
def me(usuario: CurrentUser):
    return usuario

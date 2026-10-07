import getpass
import sys
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

from database import SessionLocal
from main import inicializar_banco
from models import Usuario
from schemas import UsuarioCreate
from security import criar_hash


def main():
    inicializar_banco()
    email = input("E-mail do administrador: ").strip().lower()
    senha = getpass.getpass("Senha (mínimo de 12 caracteres): ")
    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")
    try:
        dados = UsuarioCreate(nome="Administrador", email=email, senha=senha)
    except ValidationError as error:
        raise SystemExit(f"Dados inválidos: {error}") from error
    if len(senha) < 12:
        raise SystemExit("Use uma senha com pelo menos 12 caracteres.")

    with SessionLocal() as session:
        if session.scalar(select(Usuario).where(Usuario.email == str(dados.email).lower())):
            raise SystemExit("Já existe uma conta com esse e-mail.")
        session.add(
            Usuario(
                nome=dados.nome,
                email=str(dados.email).lower(),
                senha_hash=criar_hash(dados.senha),
                ativo=True,
                admin=True,
            )
        )
        session.commit()
    print("Conta de administrador criada. Guarde a senha em um local seguro.")


if __name__ == "__main__":
    main()

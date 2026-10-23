# Forno & Folha

Aplicação web de pizzaria com catálogo, autenticação, pedidos e notificações de status de entrega.  
O backend foi construído com **FastAPI** e o armazenamento local usa **SQLite**.

## Tecnologias

- Python
- FastAPI
- SQLite
- HTML, CSS e JavaScript (frontend estático)

## Como executar localmente

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```

No arquivo `.env`, defina uma `SECRET_KEY` forte e exclusiva.  
Depois inicie a aplicação:

```bash
uvicorn main:app --reload
```

- Aplicação: `http://127.0.0.1:8000/`
- Documentação da API: `http://127.0.0.1:8000/docs`

## Funcionalidades

- Cardápio por categoria com seleção de tamanho.
- Cadastro e login em telas separadas.
- Criação de conta de cliente (sem gerar pedido automático).
- Criação e acompanhamento de pedidos com histórico.
- Cancelamento de pedidos pendentes.
- Notificações de atualização de status.
- Área de administrador para gerenciar cardápio e pedidos.

As regras de preço e de acesso ficam no servidor. Cada usuário só visualiza os próprios dados.

## Conta de administrador

O fluxo padrão cria conta de cliente. Para criar um administrador:

```bash
python scripts/criar_admin.py
```

O script solicita e-mail e senha no terminal e não grava credenciais no código.

## Teste rápido da API

```bash
python scripts/check_api.py
```

Esse script usa banco temporário em memória e não altera o banco local.

## Padrão de mensagens de commit

Para manter o histórico organizado, use um padrão simples:

- `feat: ...` para novas funcionalidades
- `fix: ...` para correções
- `docs: ...` para documentação
- `refactor: ...` para reorganização interna sem mudar comportamento
- `chore: ...` para tarefas de manutenção

Exemplos:

- `feat: adiciona filtro por categoria no cardápio`
- `fix: corrige validação de tamanho da pizza`
- `docs: atualiza instruções de execução no README`

## Segurança e uso em produção

- Nunca versione `.env` e `banco.db`.
- Mantenha o repositório privado quando houver dados reais.
- Em produção, use HTTPS, banco apropriado ao ambiente e proteção contra abuso de login.

Este projeto é focado em demonstração e ambiente local.

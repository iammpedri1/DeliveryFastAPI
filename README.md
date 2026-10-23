# Forno & Folha

Site de uma pizzaria com cardápio, contas de cliente, pedidos e avisos sobre cada etapa da entrega. A API é feita com FastAPI e salva os dados em SQLite.

## Iniciar no computador

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```

Troque `SECRET_KEY` no arquivo `.env`. Depois inicie o site:

```bash
uvicorn main:app --reload
```

Abra `http://127.0.0.1:8000/`. A documentação da API fica em `http://127.0.0.1:8000/docs`.

## O que dá para fazer

- Ver o cardápio separado por categoria e escolher entre três tamanhos.
- Entrar e criar uma conta em telas separadas.
- Criar uma conta de cliente. O cadastro não cria um pedido.
- Fazer pedidos e acompanhar seu próprio histórico. O carrinho é validado e salvo de uma vez.
- Cancelar um pedido que ainda está pendente.
- Receber avisos quando o restaurante atualizar o pedido.
- Entrar como administrador para ajustar o cardápio e os status dos pedidos.

O servidor calcula os preços e verifica quem pode ver cada pedido e notificação. Uma conta comum não pode abrir os dados de outra conta.

## Criar uma conta de administrador

O cadastro do site cria apenas contas de cliente. Para criar um administrador em uma instalação nova, rode:

```bash
python scripts/criar_admin.py
```

O programa pede o e-mail e a senha no terminal. A senha não é gravada no código. Depois, entre pela opção “Administrador” na página “Minha conta”.

## Testar os fluxos

```bash
python scripts/check_api.py
```

O script usa um banco temporário em memória e não altera as contas ou pedidos locais.

## Usar em outro computador

Para testar em dispositivos seus, instale o Tailscale nos dois computadores, conecte-os à mesma rede privada e mantenha o servidor ligado. No computador que roda a API, use `tailscale serve 8000`; abra o endereço HTTPS mostrado no outro dispositivo.

Para uma demonstração temporária, um túnel como Cloudflare Tunnel pode expor o site. Restrinja o acesso por e-mail e desligue o túnel quando terminar. Não encaminhe a porta 8000 do roteador para a internet.

## Dados e acesso ao código

O arquivo `.env` contém segredos e o arquivo `banco.db` guarda as contas. Ambos ficam fora do Git. No GitHub, mantenha o repositório como **privado** e dê acesso somente às pessoas necessárias. O código não contém a senha da conta de teste.

Para uma instalação pública, configure HTTPS, troque a chave secreta, use um banco adequado ao ambiente e limite tentativas de login. Este projeto é uma demonstração local, não um serviço pronto para receber pagamentos reais.

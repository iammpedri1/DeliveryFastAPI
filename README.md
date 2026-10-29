# Forno & Folha

Site de uma pizzaria com cardápio, contas de cliente, pedidos e avisos sobre cada etapa da entrega. A API é feita com FastAPI e salva os dados em SQLite.

## O que dá para fazer

- Ver o cardápio separado por categoria e escolher entre três tamanhos.
- Entrar e criar uma conta em telas separadas.
- Criar uma conta de cliente. O cadastro não cria um pedido.
- Fazer pedidos e acompanhar seu próprio histórico. O carrinho é validado e salvo de uma vez.
- Cancelar um pedido que ainda está pendente.
- Receber avisos quando o restaurante atualizar o pedido.
- Entrar como administrador para ajustar o cardápio e os status dos pedidos.

O servidor calcula os preços e verifica quem pode ver cada pedido e notificação. Uma conta comum não pode abrir os dados de outra conta.

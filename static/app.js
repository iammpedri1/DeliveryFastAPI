const API = location.origin;
const money = value => Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
let token = localStorage.getItem('delivery_token') || '';
let cart = JSON.parse(localStorage.getItem('delivery_cart') || '[]');
let pizzas = [];
let size = 'MEDIO';
let toastTimer;

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(API + path, { ...options, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || 'Não foi possível concluir. Tente novamente.');
  return data;
}

function notify(message, title = 'Aviso') {
  let toast = document.querySelector('#toast');
  if (!toast) {
    toast = document.createElement('aside');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.append(toast);
  }
  const heading = document.createElement('strong');
  heading.textContent = title;
  const text = document.createElement('p');
  text.textContent = message;
  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'toast-close';
  close.setAttribute('aria-label', 'Fechar aviso');
  close.textContent = 'Fechar';
  const link = document.createElement('a');
  link.href = '/site/notificacoes.html';
  link.textContent = 'Ver notificações';
  toast.replaceChildren(heading, text, link, close);
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.hidden = false;
  requestAnimationFrame(() => toast.classList.add('show'));
  close.onclick = () => { toast.classList.remove('show'); };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 6500);
}

function categoryOf(flavor) {
  return ['Margherita', 'Calabresa', 'Portuguesa'].includes(flavor) ? 'Tradicionais' : 'Especiais';
}

function renderMenu(category = 'Todas') {
  const products = document.querySelector('#products');
  if (!products) return;
  const shown = category === 'Todas' ? pizzas : pizzas.filter(pizza => categoryOf(pizza.sabor) === category);
  products.innerHTML = shown.length ? shown.map(pizza => `<article class="product"><span class="product-category">${categoryOf(pizza.sabor)}</span><h2>${escapeHtml(pizza.sabor)}</h2><p>${escapeHtml(({ Margherita: 'Molho da casa, mozzarella fresca, tomate e manjericão.', Calabresa: 'Calabresa artesanal, cebola roxa e mozzarella.', 'Quatro Queijos': 'Mozzarella, gorgonzola, parmesão e requeijão.', Portuguesa: 'Presunto, ovo, cebola, azeitona e mozzarella.' })[pizza.sabor] || 'Massa artesanal e ingredientes selecionados.')}</p><div class="product-prices"><span>Pequena <b>${money(pizza.preco_pequeno)}</b></span><span>Média <b>${money(pizza.preco_medio)}</b></span><span>Grande <b>${money(pizza.preco_grande)}</b></span></div><div class="product-bottom"><button class="add" aria-label="Adicionar ${escapeHtml(pizza.sabor)}" data-add="${pizza.id}">Adicionar tamanho escolhido</button></div></article>`).join('') : '<p class="muted">Ainda não há pizzas nesta categoria.</p>';
  products.querySelectorAll('[data-add]').forEach(button => button.onclick = () => addToCart(Number(button.dataset.add)));
}

async function initMenu() {
  try {
    pizzas = await request('/pizzas/');
    const categories = document.querySelector('#categories');
    ['Todas', 'Tradicionais', 'Especiais'].forEach((category, index) => {
      const button = document.createElement('button');
      button.className = `category${index === 0 ? ' active' : ''}`;
      button.textContent = category;
      button.onclick = () => {
        categories.querySelectorAll('button').forEach(item => item.classList.toggle('active', item === button));
        renderMenu(category);
      };
      categories.append(button);
    });
    renderMenu();
    renderCart();
    const user = token ? await request('/auth/me').catch(() => null) : null;
    if (!user && token) { token = ''; localStorage.removeItem('delivery_token'); }
    document.querySelector('#checkout-hint').textContent = user ? 'Seu pedido será associado à sua conta.' : 'Entre na sua conta para finalizar.';
    document.querySelector('#admin').style.display = user?.admin ? 'block' : 'none';
  } catch (error) { document.querySelector('#products').textContent = error.message; }
}

function addToCart(id) {
  const pizza = pizzas.find(item => item.id === id);
  if (!pizza) { notify('Esse sabor não está mais disponível. Atualize o cardápio.'); return; }
  const priceKey = `preco_${size.toLowerCase()}`;
  const price = pizza[priceKey];
  const existing = cart.find(item => item.id === id && item.size === size);
  if (existing) existing.qty++;
  else cart.push({ id, sabor: pizza.sabor, preco: Number(price), size, qty: 1 });
  renderCart();
}

function renderCart() {
  const container = document.querySelector('#cart-items');
  if (!container) return;
  container.innerHTML = cart.length ? cart.map((item, index) => `<div class="cart-line"><div><b>${item.qty}× ${escapeHtml(item.sabor)}</b><small>${({ PEQUENO: 'Individual', MEDIO: 'Média', GRANDE: 'Grande' })[item.size]}</small></div><div>${money(item.preco * item.qty)} <button class="remove" data-remove="${index}" aria-label="Remover">×</button></div></div>`).join('') : '<p class="muted">Sua sacola está vazia.</p>';
  container.querySelectorAll('[data-remove]').forEach(button => button.onclick = () => { cart.splice(Number(button.dataset.remove), 1); renderCart(); });
  document.querySelector('#cart-count').textContent = cart.reduce((sum, item) => sum + item.qty, 0);
  document.querySelector('#cart-total').textContent = money(cart.reduce((sum, item) => sum + item.preco * item.qty, 0));
  localStorage.setItem('delivery_cart', JSON.stringify(cart));
}

async function initAccount() {
  const form = document.querySelector('#account-form');
  let adminLogin = false;
  document.querySelectorAll('[data-role]').forEach(button => button.onclick = () => {
    adminLogin = button.dataset.role === 'admin';
    document.querySelectorAll('[data-role]').forEach(item => item.classList.toggle('active', item === button));
    document.querySelector('#submit-account').textContent = `Entrar como ${adminLogin ? 'administrador' : 'cliente'}`;
  });
  document.querySelector('#logout').onclick = () => { token = ''; localStorage.removeItem('delivery_token'); location.reload(); };
  try {
    const user = token ? await request('/auth/me') : null;
    if (user) {
      document.querySelector('#account-view').hidden = true;
      document.querySelector('#signed-in').hidden = false;
      document.querySelector('#greeting').textContent = `Olá, ${user.nome.split(' ')[0]}.`;
      return;
    }
  } catch { token = ''; localStorage.removeItem('delivery_token'); }
  form.onsubmit = async event => {
    event.preventDefault();
    const email = document.querySelector('#email').value.trim();
    const password = document.querySelector('#password').value;
    try {
      const login = await request('/auth/signin', { method: 'POST', body: JSON.stringify({ email, senha: password }) });
      token = login.access_token;
      const user = await request('/auth/me');
      if (Boolean(user.admin) !== adminLogin) {
        token = '';
        throw new Error(adminLogin ? 'Esta conta não tem acesso de administrador.' : 'Use a opção Administrador para entrar nesta conta.');
      }
      localStorage.setItem('delivery_token', token);
      location.href = '/site/pedidos.html';
    } catch (error) { document.querySelector('#account-message').textContent = error.message; }
  };
}

async function initSignup() {
  const form = document.querySelector('#signup-form');
  const message = document.querySelector('#signup-message');
  form.onsubmit = async event => {
    event.preventDefault();
    const nome = document.querySelector('#signup-name').value.trim();
    const email = document.querySelector('#signup-email').value.trim();
    const senha = document.querySelector('#signup-password').value;
    if (senha !== document.querySelector('#signup-confirm-password').value) {
      message.textContent = 'As senhas não coincidem.';
      return;
    }
    try {
      await request('/auth/signup', { method: 'POST', body: JSON.stringify({ nome, email, senha }) });
      const login = await request('/auth/signin', { method: 'POST', body: JSON.stringify({ email, senha }) });
      token = login.access_token;
      localStorage.setItem('delivery_token', token);
      message.textContent = 'Cadastro concluído. Abrindo sua conta...';
      setTimeout(() => { location.href = '/site/pedidos.html'; }, 800);
    } catch (error) { message.textContent = error.message; }
  };
}

async function initOrders() {
  const list = document.querySelector('#orders-list');
  if (!token) { list.innerHTML = '<p class="muted">Entre na sua conta para ver seus pedidos.</p><a class="button" href="/site/conta.html">Acessar conta</a>'; return; }
  try {
    const user = await request('/auth/me');
    const orders = await request('/pedidos/');
    if (!orders.length) { list.innerHTML = '<p class="muted">Você ainda não tem pedidos.</p>'; return; }
    const statuses = ['PENDENTE', 'EM_PREPARO', 'SAIU_PARA_ENTREGA', 'FINALIZADO', 'CANCELADO'];
    list.innerHTML = orders.map(order => `<article class="order-card"><div><b>Pedido nº ${order.id}</b><small>${user.admin ? `Conta nº ${order.usuario} · ` : ''}${order.preco ? money(order.preco) : 'Aguardando itens'}</small></div>${user.admin ? `<select data-order="${order.id}" class="status-select">${statuses.map(status => `<option ${status === order.status ? 'selected' : ''}>${status}</option>`).join('')}</select>` : order.status === 'PENDENTE' ? `<button data-cancel="${order.id}" class="cancel-button">Cancelar pedido</button>` : `<span class="status-pill">${escapeHtml(order.status.replaceAll('_', ' '))}</span>`}</article>`).join('');
    list.querySelectorAll('[data-order]').forEach(select => select.onchange = async () => {
      try { await request(`/pedidos/${select.dataset.order}/status`, { method: 'PATCH', body: JSON.stringify({ status: select.value }) }); notify('Status do pedido atualizado.'); }
      catch (error) { notify(error.message); }
    });
    list.querySelectorAll('[data-cancel]').forEach(button => button.onclick = async () => {
      try { await request(`/pedidos/${button.dataset.cancel}/cancelar`, { method: 'POST' }); notify('Pedido cancelado. Veja a notificação.'); initOrders(); }
      catch (error) { notify(error.message); }
    });
  } catch (error) { list.textContent = error.message; }
}

async function checkout() {
  if (!token) { location.href = '/site/conta.html'; return; }
  if (!cart.length) { notify('Adicione uma pizza à sacola primeiro.'); return; }
  try {
    await request('/pedidos/checkout', {
      method: 'POST',
      body: JSON.stringify({ itens: cart.map(item => ({ quantidade: item.qty, sabor: item.sabor, tamanho: item.size })) }),
    });
    cart = [];
    localStorage.removeItem('delivery_cart');
    location.href = '/site/pedidos.html';
  } catch (error) { notify(error.message); }
}

async function initNotifications() {
  const list = document.querySelector('#notifications-list');
  if (!token) { list.innerHTML = '<p class="muted">Entre na sua conta para ver suas notificações.</p><a class="button" href="/site/conta.html">Acessar conta</a>'; return; }
  try {
    const notifications = await request('/notificacoes/');
    if (!notifications.length) { list.innerHTML = '<p class="muted">Você ainda não tem notificações.</p>'; return; }
    list.innerHTML = notifications.map(item => `<article class="order-card ${item.lida ? '' : 'unread'}"><div><b>${escapeHtml(item.mensagem)}</b><small>${new Date(item.criada_em).toLocaleString('pt-BR')}${item.pedido ? ` · Pedido nº ${item.pedido}` : ''}</small></div>${item.lida ? '<span class="status-pill">Lida</span>' : `<button class="read-button" data-read="${item.id}">Marcar como lida</button>`}</article>`).join('');
    list.querySelectorAll('[data-read]').forEach(button => button.onclick = async () => {
      try { await request(`/notificacoes/${button.dataset.read}/lida`, { method: 'PATCH' }); initNotifications(); }
      catch (error) { notify(error.message); }
    });
  } catch (error) { list.textContent = error.message; }
}

async function pollNotifications() {
  if (!token) return;
  try {
    const [user, notifications] = await Promise.all([request('/auth/me'), request('/notificacoes/')]);
    const latestId = notifications[0]?.id;
    if (!latestId) return;
    const key = `delivery_last_notification_${user.id}`;
    const previousId = localStorage.getItem(key);
    if (previousId !== null && latestId > Number(previousId)) {
      const fresh = notifications.find(item => item.id > Number(previousId));
      if (fresh) notify(fresh.mensagem, 'Atualização do pedido');
    }
    localStorage.setItem(key, String(Math.max(latestId, Number(previousId) || 0)));
  } catch {
    // A tela de notificações continua acessível mesmo se a rede estiver indisponível.
  }
}

if (document.body.dataset.page === 'menu') {
  document.querySelectorAll('[data-size]').forEach(button => button.onclick = () => { size = button.dataset.size; document.querySelectorAll('[data-size]').forEach(item => item.classList.toggle('active', item === button)); });
  document.querySelector('#checkout').onclick = checkout;
  document.querySelector('#add-flavor').onclick = async () => {
    try { await request('/admin/pizzas/', { method: 'POST', body: JSON.stringify({ sabor: document.querySelector('#new-flavor').value, preco_pequeno: Number(document.querySelector('#new-small').value), preco_medio: Number(document.querySelector('#new-medium').value), preco_grande: Number(document.querySelector('#new-large').value) }) }); location.reload(); }
    catch (error) { notify(error.message); }
  };
  initMenu();
} else if (document.body.dataset.page === 'account') initAccount();
else if (document.body.dataset.page === 'signup') initSignup();
else if (document.body.dataset.page === 'orders') initOrders();
else if (document.body.dataset.page === 'notifications') {
  initNotifications();
  setInterval(initNotifications, 15000);
}

pollNotifications();
setInterval(pollNotifications, 15000);

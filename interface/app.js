"use strict";

let estado = {};
let token = "";
let pagina = "inicio";
let detalhe = null;
let timerToast;
const $ = (seletor) => document.querySelector(seletor);
const esc = (valor) => String(valor ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c]));
const dinheiro = (valor) => Number(valor).toLocaleString("pt-BR", {style:"currency", currency:"BRL"});

const logo = $("#brand-logo");
logo.addEventListener("load", () => {
  logo.hidden = false;
  $("#brand-fallback").hidden = true;
});
logo.src = "/logo.png";

function aviso(texto, erro = false) {
  const toast = $("#toast");
  toast.textContent = texto;
  toast.className = erro ? "show error" : "show";
  clearTimeout(timerToast);
  timerToast = setTimeout(() => { toast.className = ""; }, 3600);
}

async function atualizar() {
  const resposta = await fetch("/api/estado");
  if (!resposta.ok) throw new Error("Não foi possível conectar ao EventFlow.");
  const dados = await resposta.json();
  token = dados.token;
  estado = dados.estado;
}

function registrarPresenca() {
  return fetch("/api/presenca", {method:"POST", headers:{"X-EventFlow-Token":token}})
    .catch(() => {});
}

async function acao(nome, dados = {}) {
  const resposta = await fetch("/api/acao", {method:"POST", headers:{"Content-Type":"application/json", "X-EventFlow-Token":token}, body:JSON.stringify({acao:nome, dados})});
  const resultado = await resposta.json();
  if (!resposta.ok) throw new Error(resultado.erro || "Não foi possível concluir a ação.");
  estado = resultado.estado;
  return resultado.resultado;
}

function botao(texto, comando, classe = "", extras = "") {
  return `<button type="button" class="btn ${classe}" data-action="${comando}" ${extras}>${texto}</button>`;
}
function cabecalho(titulo, descricao, extra = "", olho = "EVENTFLOW") {
  return `<div class="heading"><div><p class="eyebrow">${olho}</p><h1>${titulo}</h1><p class="subtitle">${descricao}</p></div>${extra}</div>`;
}
function vazio(titulo, descricao) { return `<div class="empty"><strong>${titulo}</strong>${descricao}</div>`; }
function status(texto) {
  const cor = ["Publicado", "Confirmada", "Ativa"].includes(texto) ? "green" : ["Cancelado", "Cancelada"].includes(texto) ? "red" : texto === "Lista de espera" ? "yellow" : "";
  return `<span class="pill ${cor}">${esc(texto)}</span>`;
}
function tabela(cabecalhos, linhas, mensagem = "Nenhum registro encontrado.") {
  if (!linhas.length) return vazio("Tudo tranquilo por aqui", mensagem);
  return `<div class="table-wrap"><table><thead><tr>${cabecalhos.map(c => `<th>${c}</th>`).join("")}</tr></thead><tbody>${linhas.map(l => `<tr>${l.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function nav() {
  const itens = [["inicio", "⌂", "Início"], ["explorar", "◈", "Explorar eventos"]];
  if (estado.usuario?.tipo === "organizador") itens.push(["eventos", "▦", "Meus eventos"], ["equipes", "♧", "Equipes"], ["relatorio", "▤", "Relatório"]);
  if (estado.usuario?.tipo === "participante") itens.push(["inscricoes", "◷", "Minhas inscrições"]);
  if (estado.usuario) itens.push(["perfil", "◉", "Meu perfil"], ["sair", "↪", "Sair da conta"]);
  else itens.push(["login", "↪", "Entrar"], ["cadastro", "＋", "Criar conta"]);
  $("#nav").innerHTML = itens.map(([id, icone, texto]) => `<button type="button" class="nav-btn ${pagina === id ? "active" : ""}" data-nav="${id}"><span class="nav-icon">${icone}</span>${texto}</button>`).join("");
  $("#account").innerHTML = estado.usuario ? `<span>${esc(estado.usuario.nome)}</span><span class="avatar">${esc(estado.usuario.nome.charAt(0).toUpperCase())}</span>` : `<span>Bem-vindo ao EventFlow</span><span class="avatar">✦</span>`;
  $("#breadcrumb").textContent = "VISÃO GERAL / " + (itens.find(i => i[0] === pagina)?.[2] || "Início").toUpperCase();
}

function linhasEventos(eventos, gerenciar = false) {
  return eventos.map(e => [esc(e.titulo), esc(e.data_hora), esc(e.local), status(e.status), `${e.disponiveis} de ${e.vagas}`, botao(gerenciar ? "Gerenciar" : "Detalhes", "detalhes", "small", `data-id="${e.id}" data-gerenciar="${gerenciar}"`)]);
}
function render() {
  nav();
  const usuario = estado.usuario;
  let html = "";
  if (pagina === "inicio") {
    const nome = usuario ? esc(usuario.nome.split(" ")[0]) : "você";
    const quantidade = usuario?.tipo === "organizador" ? (estado.meus_eventos || []).length : usuario?.tipo === "participante" ? (estado.inscricoes || []).length : "—";
    const titulo = usuario?.tipo === "organizador" ? "Meus eventos" : usuario?.tipo === "participante" ? "Minhas inscrições" : "Sua jornada";
    html = cabecalho(`Olá, ${nome} <span class="muted">✦</span>`, "Tudo pronto para o seu próximo encontro?", "", "SEU PAINEL") +
      `<section class="hero"><div class="hero-copy"><p class="eyebrow">MOMENTOS QUE CONECTAM</p><h2>Grandes ideias merecem<br>grandes eventos.</h2><p>Descubra, planeje e acompanhe eventos em um só lugar.</p>${botao("Explorar eventos →", "navegar-explorar", "primary")}</div><div class="hero-art" aria-hidden="true"><div class="art-ring"></div><div class="art-card"><b>✦</b><i></i><i></i></div><span class="art-spark">✧</span></div></section>
      <div class="metrics"><div class="metric"><div><span>Eventos publicados</span><strong>${estado.publicados.length}</strong></div><div class="metric-icon">▦</div></div><div class="metric"><div><span>Equipes cadastradas</span><strong>${estado.equipes_total}</strong></div><div class="metric-icon">♧</div></div><div class="metric"><div><span>${titulo}</span><strong>${quantidade}</strong></div><div class="metric-icon">✧</div></div></div>
      <div class="section-title"><h2>Eventos em destaque</h2><a data-nav="explorar">Ver todos →</a></div><div class="panel">${tabela(["Evento", "Data e hora", "Local", "Status", "Vagas livres", ""], linhasEventos(estado.publicados.slice(0, 4)), "Os eventos publicados aparecerão aqui.")}</div>
      <div class="section-title toolbar"><h2>Ferramentas</h2></div><div class="button-row">${!usuario ? botao("Entrar", "login", "primary") + botao("Criar conta", "cadastro") : ""}${botao("Carregar demonstração", "demo")}${botao("Resumo do banco", "resumo")}</div>`;
  } else if (pagina === "explorar") {
    html = cabecalho("Explorar eventos", "Descubra eventos publicados e consulte os detalhes.", "", "DESCUBRA") + `<div class="panel">${tabela(["Evento", "Data e hora", "Local", "Status", "Vagas livres", ""], linhasEventos(estado.publicados), "Quando houver eventos publicados, eles aparecerão aqui.")}</div>`;
  } else if (pagina === "eventos" && usuario?.tipo === "organizador") {
    html = cabecalho("Meus eventos", "Crie, acompanhe e gerencie seus eventos.", botao("＋ Criar evento", "criar-evento", "primary"), "ORGANIZAÇÃO") + `<div class="panel">${tabela(["Evento", "Data e hora", "Local", "Status", "Vagas livres", ""], linhasEventos(estado.meus_eventos, true), "Crie seu primeiro evento para começar.")}</div>`;
  } else if (pagina === "equipes" && usuario?.tipo === "organizador") {
    const linhas = estado.equipes.map(e => [esc(e.nome), esc(e.servicos), dinheiro(e.preco)]);
    html = cabecalho("Equipes de divulgação", "Cadastre parceiros e consulte os serviços disponíveis.", botao("＋ Cadastrar equipe", "cadastrar-equipe", "primary"), "PARCEIROS") + `<div class="panel">${tabela(["Equipe", "Serviços", "Preço"], linhas, "Cadastre equipes para contratá-las em eventos publicados.")}</div>`;
  } else if (pagina === "inscricoes" && usuario?.tipo === "participante") {
    const linhas = estado.inscricoes.map(i => [esc(i.titulo), esc(i.data_hora), status(i.status), status(i.evento_status), i.status !== "Cancelada" ? botao("Cancelar interesse", "cancelar-inscricao", "small", `data-id="${i.evento_id}"`) : "—"]);
    html = cabecalho("Minhas inscrições", "Acompanhe sua participação e a lista de espera.", "", "PARTICIPAÇÃO") + `<div class="panel">${tabela(["Evento", "Data e hora", "Inscrição", "Evento", ""], linhas, "Explore eventos para demonstrar interesse.")}</div>`;
  } else if (pagina === "relatorio" && usuario?.tipo === "organizador") {
    const linhas = estado.meus_eventos.map(e => [esc(e.titulo), status(e.status), `${e.confirmados} / ${e.vagas}`, e.espera]);
    html = cabecalho("Relatório", "Uma visão dos eventos que você organiza.", "", "ACOMPANHAMENTO") + `<div class="panel">${tabela(["Evento", "Status", "Confirmados / vagas", "Na lista de espera"], linhas, "Crie eventos para visualizar seu relatório.")}</div>`;
  } else if (pagina === "perfil" && usuario) {
    html = cabecalho("Meu perfil", "Informações da sua conta.", "", "MINHA CONTA") + `<div class="panel panel-pad"><div class="profile-line">Nome<strong>${esc(usuario.nome)}</strong></div><div class="profile-line">E-mail<strong>${esc(usuario.email)}</strong></div><div class="profile-line">Perfil<strong>${esc(usuario.tipo === "organizador" ? "Organizador" : "Participante")}</strong></div></div>`;
  } else { pagina = "inicio"; return render(); }
  $("#content").innerHTML = html;
}

function mostrarModal(titulo, conteudo, largo = false) {
  const modal = $("#modal");
  modal.classList.toggle("wide", largo);
  $("#modal-content").innerHTML = `<div class="modal-top"><div><p class="eyebrow">EVENTFLOW</p><h2 id="modal-title">${titulo}</h2></div><button type="button" class="close" aria-label="Fechar" data-action="fechar">×</button></div>${conteudo}`;
  if (!modal.open) modal.showModal();
}
function fechar() { $("#modal").close(); detalhe = null; }
function campo(nome, rotulo, valor = "", tipo = "text", opcoes = null, cheio = false) {
  let entrada;
  if (opcoes) entrada = `<select id="${nome}" name="${nome}" required>${opcoes.map(([v, t]) => `<option value="${esc(v)}" ${String(v) === String(valor) ? "selected" : ""}>${esc(t)}</option>`).join("")}</select>`;
  else if (tipo === "textarea") entrada = `<textarea id="${nome}" name="${nome}" required>${esc(valor)}</textarea>`;
  else entrada = `<input id="${nome}" name="${nome}" type="${tipo}" value="${esc(valor)}" required ${tipo === "number" ? 'min="1" step="1"' : ""}>`;
  return `<div class="field ${cheio ? "full" : ""}"><label for="${nome}">${rotulo}</label>${entrada}</div>`;
}
function formulario(titulo, tipo, campos, voltar = false) {
  mostrarModal(titulo, `<form id="formulario" data-form="${tipo}"><div class="form-grid">${campos}</div><div class="modal-actions">${botao("Cancelar", voltar ? "voltar-detalhes" : "fechar")}<button class="btn primary" type="submit">Salvar</button></div></form>`);
}
function formConta(tipo) {
  detalhe = null;
  const cadastro = tipo === "cadastro";
  formulario(cadastro ? "Criar conta" : "Entrar na conta", tipo,
    (cadastro ? campo("nome", "Nome", "", "text", null, true) : "") + campo("email", "E-mail", "", "email", null, true) + campo("senha", "Senha", "", "password", null, true) +
    (cadastro ? campo("tipo", "Perfil", "participante", "text", [["participante", "Participante"], ["organizador", "Organizador"]], true) : ""));
}
function formEvento(evento = null) {
  const e = evento || {};
  formulario(evento ? "Editar evento" : "Criar evento", evento ? "editar_evento" : "criar_evento",
    campo("titulo", "Título", e.titulo, "text", null, true) + campo("descricao", "Descrição", e.descricao, "textarea", null, true) +
    (evento && !e.data_hora_input ? `<div class="notice field full">Data anterior: ${esc(e.data_hora)}. Selecione uma data e hora válidas para salvar.</div>` : "") +
    campo("data_hora", "Data e hora", e.data_hora_input || "", "datetime-local", null, true) +
    campo("local", "Local", e.local) + campo("categoria", "Categoria", e.categoria) + campo("vagas", "Número de vagas", e.vagas, "number"), Boolean(evento));
}
function eventoDetalhe(id, gerenciar) {
  const evento = (gerenciar ? estado.meus_eventos : estado.publicados)?.find(e => e.id === id);
  if (!evento) { fechar(); render(); aviso("Evento indisponível.", true); return; }
  detalhe = {id, gerenciar};
  let botoes = "";
  if (gerenciar && evento.status !== "Cancelado") botoes = botao("Editar", "editar-evento") + (evento.status === "Rascunho" ? botao("Publicar evento", "publicar-evento", "primary") : "") + botao("Cancelar evento", "cancelar-evento", "danger");
  else if (estado.usuario?.tipo === "participante") botoes = botao("Demonstrar interesse", "inscrever", "primary");
  let conteudo = `<div class="modal-body"><p>${esc(evento.descricao)}</p><div class="detail-grid"><div class="detail-box"><span>Quando</span>${esc(evento.data_hora)}</div><div class="detail-box"><span>Onde</span>${esc(evento.local)}</div><div class="detail-box"><span>Organizador</span>${esc(evento.organizador)}</div><div class="detail-box"><span>Categoria e situação</span>${esc(evento.categoria)} · ${status(evento.status)}</div><div class="detail-box"><span>Confirmados</span>${evento.confirmados} de ${evento.vagas} vagas</div><div class="detail-box"><span>Lista de espera</span>${evento.espera} pessoa(s)</div></div><div class="button-row">${botoes}</div>`;
  if (gerenciar) {
    const inscricoes = evento.inscricoes.map(i => [esc(i.nome), esc(i.email), status(i.status)]);
    const contratacoes = evento.contratacoes.map(c => [esc(c.equipe), dinheiro(c.preco), status(c.status), c.status === "Ativa" ? botao("Substituir", "substituir", "small", `data-id="${c.id}"`) + " " + botao("Cancelar", "cancelar-contratacao", "small danger", `data-id="${c.id}"`) : "—"]);
    conteudo += `<div class="detail-section"><h3>Inscrições</h3><div class="panel">${tabela(["Participante", "E-mail", "Situação"], inscricoes, "Ainda não há inscrições.")}</div></div><div class="detail-section"><div class="section-title"><h3>Equipes contratadas</h3>${evento.status === "Publicado" ? botao("＋ Contratar equipe", "contratar", "small") : ""}</div><div class="panel">${tabela(["Equipe", "Preço", "Situação", ""], contratacoes, "Nenhuma contratação registrada.")}</div></div>`;
  } else {
    conteudo += `<p>Equipes de divulgação: ${esc(evento.equipes_ativas.join(", ") || "nenhuma")}</p>${!estado.usuario ? '<div class="notice">Entre como participante para demonstrar interesse.</div>' : ""}`;
  }
  mostrarModal(esc(evento.titulo), conteudo + "</div>", true);
}
function formEquipeContratada(contratacaoId = null) {
  if (!estado.equipes.length) { aviso("Cadastre uma equipe no menu Equipes primeiro.", true); return; }
  const opcoes = estado.equipes.map(e => [e.id, `${e.nome} · ${dinheiro(e.preco)}`]);
  formulario(contratacaoId === null ? "Contratar equipe" : "Substituir equipe", contratacaoId === null ? "contratar" : `substituir:${contratacaoId}`,
    campo("equipe_id", "Equipe de divulgação", opcoes[0][0], "text", opcoes, true), true);
}

document.addEventListener("click", async (evento) => {
  const alvo = evento.target.closest("[data-action], [data-nav]");
  if (!alvo) return;
  const navId = alvo.dataset.nav;
  if (navId) {
    if (["login", "cadastro"].includes(navId)) return formConta(navId);
    if (navId === "sair") {
      try { await acao("sair"); pagina = "inicio"; render(); aviso("Você saiu da conta."); } catch (e) { aviso(e.message, true); }
      return;
    }
    pagina = navId; render(); return;
  }
  const nome = alvo.dataset.action;
  try {
    if (nome === "navegar-explorar") { pagina = "explorar"; render(); }
    else if (["login", "cadastro"].includes(nome)) formConta(nome);
    else if (nome === "fechar") fechar();
    else if (nome === "voltar-detalhes") eventoDetalhe(detalhe.id, detalhe.gerenciar);
    else if (nome === "detalhes") eventoDetalhe(Number(alvo.dataset.id), alvo.dataset.gerenciar === "true");
    else if (nome === "criar-evento") { detalhe = null; formEvento(); }
    else if (nome === "editar-evento") formEvento(estado.meus_eventos.find(e => e.id === detalhe.id));
    else if (nome === "cadastrar-equipe") formulario("Cadastrar equipe", "cadastrar_equipe", campo("nome", "Nome", "", "text", null, true) + campo("servicos", "Serviços oferecidos", "", "text", null, true) + campo("preco", "Preço em reais (ex.: 250,00)", "", "text", null, true));
    else if (nome === "contratar") formEquipeContratada();
    else if (nome === "substituir") formEquipeContratada(Number(alvo.dataset.id));
    else if (nome === "demo") {
      if (confirm("Adicionar contas, equipes e um evento de demonstração?")) { await acao("demo"); render(); aviso("Dados de demonstração carregados. Senha: 123."); }
    } else if (nome === "resumo") {
      const dados = await acao("resumo");
      mostrarModal("Resumo do banco", `<div class="modal-body">${Object.entries(dados).map(([chave, valor]) => `<div class="profile-line">${esc(chave)}<strong>${valor} registro(s)</strong></div>`).join("")}</div>`);
    } else if (nome === "cancelar-inscricao") {
      if (confirm("Cancelar seu interesse neste evento?")) { await acao("cancelar_inscricao", {evento_id:Number(alvo.dataset.id)}); render(); aviso("Interesse cancelado."); }
    } else if (nome === "publicar-evento") {
      await acao("publicar_evento", {evento_id:detalhe.id}); render(); eventoDetalhe(detalhe.id, true); aviso("Evento publicado.");
    } else if (nome === "cancelar-evento") {
      if (confirm("Cancelar este evento e suas inscrições e contratações ativas?")) { await acao("cancelar_evento", {evento_id:detalhe.id}); render(); eventoDetalhe(detalhe.id, true); aviso("Evento cancelado."); }
    } else if (nome === "inscrever") {
      const resultado = await acao("inscrever", {evento_id:detalhe.id}); render(); eventoDetalhe(detalhe.id, false); aviso(`Inscrição registrada: ${resultado.status}.`);
    } else if (nome === "cancelar-contratacao") {
      if (confirm("Cancelar esta contratação?")) { await acao("cancelar_contratacao", {evento_id:detalhe.id, contratacao_id:Number(alvo.dataset.id)}); render(); eventoDetalhe(detalhe.id, true); aviso("Contratação cancelada."); }
    }
  } catch (erro) { aviso(erro.message, true); }
});

document.addEventListener("submit", async (evento) => {
  if (evento.target.id !== "formulario") return;
  evento.preventDefault();
  const form = evento.target;
  const botaoSalvar = form.querySelector('[type="submit"]');
  botaoSalvar.disabled = true;
  const dados = Object.fromEntries(new FormData(form));
  let tipo = form.dataset.form;
  if (tipo === "editar_evento") dados.evento_id = detalhe.id;
  if (tipo === "contratar" || tipo.startsWith("substituir:")) {
    dados.evento_id = detalhe.id; dados.equipe_id = Number(dados.equipe_id);
    if (tipo.startsWith("substituir:")) { dados.contratacao_id = Number(tipo.split(":")[1]); tipo = "substituir"; }
  }
  try {
    await acao(tipo, dados);
    render();
    if (["editar_evento", "contratar", "substituir"].includes(tipo)) eventoDetalhe(detalhe.id, true);
    else { fechar(); if (["login", "cadastro"].includes(tipo)) { pagina = "inicio"; render(); } }
    aviso(tipo === "login" ? "Bem-vindo de volta!" : "Alteração salva com sucesso.");
  } catch (erro) { aviso(erro.message, true); botaoSalvar.disabled = false; }
});

atualizar().then(() => {
  render();
  registrarPresenca();
  setInterval(registrarPresenca, 10000);
}).catch(erro => { $("#content").innerHTML = `<div class="panel panel-pad">${esc(erro.message)}</div>`; });

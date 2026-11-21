"use strict";

// Exercita a interface sem abrir uma janela nem iniciar um servidor.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const elementos = {};
const requisicoes = [];
const documento = {
  querySelector(seletor) {
    return elementos[seletor] ||= {
      hidden: false,
      innerHTML: "",
      open: false,
      classList: {toggle() {}},
      addEventListener() {},
      showModal() { this.open = true; },
      close() { this.open = false; },
    };
  },
  addEventListener() {},
};

const codigo = fs.readFileSync(path.join(__dirname, "interface", "app.js"), "utf8");
const verificacoes = `
  const eventoTeste = {id: 1, titulo: "Evento", descricao: "Descrição", data_hora: "20/12/2026 às 18:30",
    data_hora_input: "2026-12-20T18:30", local: "Praça", categoria: "Cultura", status: "Cancelado",
    confirmados: 0, vagas: 1, espera: 0, organizador: "Ana", inscricoes: [], contratacoes: []};
  estado = {usuario: {tipo: "organizador"}, meus_eventos: [eventoTeste]};
  eventoDetalhe(1, true);
  let html = document.querySelector("#modal-content").innerHTML;
  assert.doesNotMatch(html, /data-action="editar-evento"/);
  assert.doesNotMatch(html, /data-action="cancelar-evento"/);
  eventoTeste.status = "Rascunho";
  eventoDetalhe(1, true);
  html = document.querySelector("#modal-content").innerHTML;
  assert.match(html, /data-action="editar-evento"/);
  formEvento(eventoTeste);
  html = document.querySelector("#modal-content").innerHTML;
  assert.match(html, /type="datetime-local"/);
  assert.match(html, /value="2026-12-20T18:30"/);
  eventoTeste.data_hora_input = "";
  eventoTeste.data_hora = "data antiga";
  formEvento(eventoTeste);
  assert.match(document.querySelector("#modal-content").innerHTML, /data antiga/);
  token = "segredo";
  registrarPresenca();
  assert.equal(requisicoes[0].url, "/api/presenca");
  assert.equal(requisicoes[0].opcoes.headers["X-EventFlow-Token"], "segredo");
`;

vm.runInNewContext(codigo + verificacoes, {
  assert,
  document: documento,
  requisicoes,
  fetch: (url, opcoes) => {
    if (url === "/api/estado") return new Promise(() => {});
    requisicoes.push({url, opcoes});
    return Promise.resolve({ok: true});
  },
  setTimeout,
  clearTimeout,
});

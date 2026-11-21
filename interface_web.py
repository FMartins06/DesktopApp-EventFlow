"""Servidor local e ponte entre a interface HTML e o domínio do EventFlow."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aplicacao import SistemaEventFlow
from modelos import Organizador, Participante, StatusEvento, interpretar_data_hora


PASTA_INTERFACE = Path(__file__).with_name("interface")


class AplicacaoWeb:
    """Oferece operações à interface e mantém a sessão nesta execução."""

    def __init__(self, sistema):
        self.sistema = sistema
        self.usuario = None

    def _exigir(self, tipo):
        if not isinstance(self.usuario, tipo):
            raise PermissionError("Entre com o perfil adequado para realizar esta ação.")
        return self.usuario

    def _evento(self, identificador, proprio=False):
        evento = next((e for e in self.sistema.eventos if e.id_banco == identificador), None)
        if evento is None or (proprio and evento.organizador is not self.usuario):
            raise ValueError("Evento não encontrado.")
        if not proprio and evento.status != StatusEvento.PUBLICADO:
            raise ValueError("Evento não disponível.")
        return evento

    def _equipe(self, identificador):
        equipe = next((e for e in self.sistema.equipes if e.id_banco == identificador), None)
        if equipe is None:
            raise ValueError("Equipe não encontrada.")
        return equipe

    def _contratacao(self, evento, identificador):
        item = next((c for c in evento.contratacoes if c.id_banco == identificador), None)
        if item is None:
            raise ValueError("Contratação não encontrada.")
        return item

    @staticmethod
    def _dados_evento(evento, incluir_privado=False):
        dados = {
            "id": evento.id_banco, "titulo": evento.titulo,
            "descricao": evento.descricao, "data_hora": evento.data_hora,
            "local": evento.local, "categoria": evento.categoria,
            "vagas": evento.vagas, "disponiveis": evento.vagas_disponiveis,
            "confirmados": evento.total_confirmados, "status": evento.status.value,
            "organizador": evento.organizador.nome,
            "espera": sum(i.status.value == "Lista de espera" for i in evento.inscricoes),
            "equipes_ativas": [c.equipe.nome for c in evento.contratacoes if c.status.value == "Ativa"],
        }
        if incluir_privado:
            try:
                dados["data_hora_input"] = interpretar_data_hora(evento.data_hora).strftime("%Y-%m-%dT%H:%M")
            except ValueError:
                dados["data_hora_input"] = ""
            dados["inscricoes"] = [{"nome": i.participante.nome, "email": i.participante.email,
                                    "status": i.status.value} for i in evento.inscricoes]
            dados["contratacoes"] = [{"id": c.id_banco, "equipe": c.equipe.nome,
                                      "preco": c.equipe.preco, "status": c.status.value}
                                     for c in evento.contratacoes]
        return dados

    def estado(self):
        usuario = self.usuario
        dados = {"usuario": None, "publicados": [self._dados_evento(e) for e in self.sistema.eventos_publicados],
                 "equipes_total": len(self.sistema.equipes)}
        if usuario:
            dados["usuario"] = {"nome": usuario.nome, "email": usuario.email,
                                "tipo": "organizador" if isinstance(usuario, Organizador) else "participante",
                                "perfil": usuario.descricao_perfil()}
        if isinstance(usuario, Organizador):
            dados["meus_eventos"] = [self._dados_evento(e, True) for e in usuario.eventos]
            dados["equipes"] = [{"id": e.id_banco, "nome": e.nome, "servicos": e.servicos,
                                  "preco": e.preco} for e in self.sistema.equipes]
        elif isinstance(usuario, Participante):
            dados["inscricoes"] = [{"evento_id": e.id_banco, "titulo": e.titulo,
                                    "data_hora": e.data_hora, "status": i.status.value,
                                    "evento_status": e.status.value}
                                   for e, i in self.sistema.inscricoes_de(usuario)]
        return dados

    def executar(self, acao, dados):
        if acao == "login":
            self.usuario = self.sistema.usuarios.autenticar(dados["email"], dados["senha"])
        elif acao == "cadastro":
            self.usuario = self.sistema.cadastrar_usuario(dados["nome"], dados["email"], dados["senha"], dados["tipo"])
        elif acao == "sair":
            self.usuario = None
        elif acao == "demo":
            self.sistema.carregar_dados_demo()
        elif acao == "resumo":
            return self.sistema.resumo_banco()
        elif acao in ("criar_evento", "editar_evento"):
            usuario = self._exigir(Organizador)
            vagas = int(dados["vagas"])
            valores = (dados["titulo"], dados["descricao"], dados["data_hora"],
                       dados["local"], dados["categoria"], vagas)
            if acao == "criar_evento":
                self.sistema.criar_evento(usuario, *valores)
            else:
                self.sistema.editar_evento(usuario, self._evento(dados["evento_id"], True), *valores)
        elif acao in ("publicar_evento", "cancelar_evento"):
            usuario = self._exigir(Organizador)
            evento = self._evento(dados["evento_id"], True)
            if acao == "publicar_evento":
                self.sistema.publicar_evento(usuario, evento)
            else:
                self.sistema.cancelar_evento(usuario, evento)
        elif acao == "cadastrar_equipe":
            self._exigir(Organizador)
            preco = float(str(dados["preco"]).replace(",", "."))
            if not math.isfinite(preco):
                raise ValueError("Informe um preço válido.")
            self.sistema.cadastrar_equipe(dados["nome"], dados["servicos"], preco)
        elif acao in ("contratar", "cancelar_contratacao", "substituir"):
            usuario = self._exigir(Organizador)
            evento = self._evento(dados["evento_id"], True)
            if acao == "contratar":
                self.sistema.contratar_equipe(usuario, evento, self._equipe(dados["equipe_id"]))
            else:
                contratacao = self._contratacao(evento, dados["contratacao_id"])
                if acao == "cancelar_contratacao":
                    self.sistema.cancelar_contratacao(usuario, evento, contratacao)
                else:
                    self.sistema.substituir_equipe(usuario, evento, contratacao, self._equipe(dados["equipe_id"]))
        elif acao == "inscrever":
            participante = self._exigir(Participante)
            inscricao = self.sistema.demonstrar_interesse(self._evento(dados["evento_id"]), participante)
            return {"status": inscricao.status.value}
        elif acao == "cancelar_inscricao":
            participante = self._exigir(Participante)
            evento = next((e for e, i in self.sistema.inscricoes_de(participante)
                           if e.id_banco == dados["evento_id"] and i.status.value != "Cancelada"), None)
            if evento is None:
                raise ValueError("Inscrição ativa não encontrada.")
            self.sistema.cancelar_interesse(evento, participante)
        else:
            raise ValueError("Ação desconhecida.")
        return {"ok": True}


class ServidorEventFlow(HTTPServer):
    def __init__(self, endereco, sistema):
        super().__init__(endereco, Requisicoes)
        self.aplicacao = AplicacaoWeb(sistema)
        self.token = secrets.token_urlsafe(32)


class Requisicoes(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        pass

    def _responder(self, codigo, conteudo, tipo="application/json; charset=utf-8"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(conteudo)

    def _json(self, codigo, dados):
        self._responder(codigo, json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _host_valido(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self._host_valido():
            return self._json(403, {"erro": "Origem inválida."})
        if self.path == "/api/estado":
            return self._json(200, {"token": self.server.token, "estado": self.server.aplicacao.estado()})
        arquivos = {"/": ("index.html", "text/html; charset=utf-8"),
                    "/style.css": ("style.css", "text/css; charset=utf-8"),
                    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                    "/logo.png": ("logo.png", "image/png")}
        if self.path not in arquivos:
            return self._json(404, {"erro": "Página não encontrada."})
        arquivo, tipo = arquivos[self.path]
        if not (PASTA_INTERFACE / arquivo).is_file():
            return self._json(404, {"erro": "Arquivo não encontrado."})
        self._responder(200, (PASTA_INTERFACE / arquivo).read_bytes(), tipo)

    def do_POST(self):
        origem = f"http://127.0.0.1:{self.server.server_port}"
        if (not self._host_valido() or self.headers.get("Origin") != origem or
                not secrets.compare_digest(self.headers.get("X-EventFlow-Token", ""), self.server.token)):
            return self._json(403, {"erro": "Requisição não autorizada."})
        if self.path != "/api/acao":
            return self._json(404, {"erro": "Ação não encontrada."})
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= 65536:
                raise ValueError("Requisição inválida.")
            requisicao = json.loads(self.rfile.read(tamanho))
            resultado = self.server.aplicacao.executar(requisicao["acao"], requisicao.get("dados", {}))
            self._json(200, {"resultado": resultado, "estado": self.server.aplicacao.estado()})
        except (ValueError, TypeError, KeyError, PermissionError, sqlite3.Error) as erro:
            self._json(400, {"erro": str(erro) or "Dados inválidos."})


def localizar_navegador():
    caminhos = []
    if sys.platform == "win32":
        for raiz in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES"), os.environ.get("LOCALAPPDATA")):
            if raiz:
                caminhos.extend([Path(raiz) / "Microsoft/Edge/Application/msedge.exe",
                                 Path(raiz) / "Google/Chrome/Application/chrome.exe"])
    for nome in ("microsoft-edge", "microsoft-edge-stable", "google-chrome", "chromium", "chromium-browser"):
        encontrado = shutil.which(nome)
        if encontrado:
            caminhos.append(Path(encontrado))
    return next((str(c) for c in caminhos if c.is_file()), None)


def executar(caminho_banco=None):
    navegador = localizar_navegador()
    if not navegador:
        raise SystemExit("Instale o Microsoft Edge, Google Chrome ou Chromium para abrir a interface gráfica.")
    sistema = SistemaEventFlow() if caminho_banco is None else SistemaEventFlow(caminho_banco)
    servidor = ServidorEventFlow(("127.0.0.1", 0), sistema)
    endereco = f"http://127.0.0.1:{servidor.server_port}/"
    with tempfile.TemporaryDirectory(prefix="eventflow-") as perfil:
        try:
            processo = subprocess.Popen([navegador, f"--app={endereco}", f"--user-data-dir={perfil}",
                                         "--no-first-run", "--no-default-browser-check"])
            def aguardar_janela():
                processo.wait()
                servidor.shutdown()
            threading.Thread(target=aguardar_janela, daemon=True).start()
            servidor.serve_forever()
        finally:
            servidor.server_close()
            sistema.banco.fechar()

"""Persistência SQLite do EventFlow.

O banco usa tabelas relacionais e chaves estrangeiras. A camada de domínio
continua responsável pelas regras de negócio; esta classe apenas reconstrói e
salva o grafo de objetos em uma transação.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterable

from modelos import (
    ContratacaoDivulgacao,
    EquipeDivulgacao,
    Evento,
    GerenciadorUsuarios,
    Inscricao,
    Organizador,
    Participante,
    StatusContratacao,
    StatusEvento,
    StatusInscricao,
    Usuario,
)


CAMINHO_SCHEMA = Path(__file__).with_name("schema.sql")


class BancoDados:
    """Cria o esquema e persiste o estado do sistema em SQLite."""

    TABELAS = ("usuarios", "eventos", "equipes", "inscricoes", "contratacoes")

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = str(caminho)
        self._conexao = sqlite3.connect(self.caminho)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA foreign_keys = ON")
        if self.caminho != ":memory:":
            self._conexao.execute("PRAGMA journal_mode = WAL")
        self._criar_esquema()

    def _criar_esquema(self) -> None:
        script_sql = CAMINHO_SCHEMA.read_text(encoding="utf-8")
        self._conexao.executescript(script_sql)
        self._conexao.commit()

    def carregar(self) -> tuple[GerenciadorUsuarios, list[EquipeDivulgacao]]:
        """Reconstrói todos os objetos e suas relações a partir das tabelas."""
        usuarios = GerenciadorUsuarios()
        usuarios_por_id: dict[int, Usuario] = {}

        for linha in self._conexao.execute("SELECT * FROM usuarios ORDER BY id"):
            usuario = usuarios.restaurar(
                id_banco=linha["id"],
                nome=linha["nome"],
                email=linha["email"],
                tipo=linha["tipo"],
                senha_hash=linha["senha_hash"],
                senha_salt=linha["senha_salt"],
            )
            usuarios_por_id[linha["id"]] = usuario

        equipes: list[EquipeDivulgacao] = []
        equipes_por_id: dict[int, EquipeDivulgacao] = {}
        for linha in self._conexao.execute("SELECT * FROM equipes ORDER BY id"):
            equipe = EquipeDivulgacao(
                linha["nome"],
                linha["servicos"],
                linha["preco"],
                id_banco=linha["id"],
            )
            equipes.append(equipe)
            equipes_por_id[linha["id"]] = equipe

        eventos_por_id: dict[int, Evento] = {}
        for linha in self._conexao.execute("SELECT * FROM eventos ORDER BY id"):
            organizador = usuarios_por_id[linha["organizador_id"]]
            if not isinstance(organizador, Organizador):
                raise RuntimeError("Evento associado a um usuário não organizador.")
            evento = organizador.criar_evento(
                titulo=linha["titulo"],
                descricao=linha["descricao"],
                data_hora=linha["data_hora"],
                local=linha["local"],
                categoria=linha["categoria"],
                vagas=linha["vagas"],
            )
            evento.id_banco = linha["id"]
            evento.status = StatusEvento[linha["status"]]
            eventos_por_id[linha["id"]] = evento

        consulta_inscricoes = "SELECT * FROM inscricoes ORDER BY evento_id, ordem"
        for linha in self._conexao.execute(consulta_inscricoes):
            participante = usuarios_por_id[linha["participante_id"]]
            if not isinstance(participante, Participante):
                raise RuntimeError("Inscrição associada a um não participante.")
            inscricao = Inscricao(
                participante=participante,
                status=StatusInscricao[linha["status"]],
                id_banco=linha["id"],
            )
            eventos_por_id[linha["evento_id"]]._inscricoes.append(inscricao)

        consulta_contratacoes = "SELECT * FROM contratacoes ORDER BY evento_id, ordem"
        for linha in self._conexao.execute(consulta_contratacoes):
            contratacao = ContratacaoDivulgacao(
                equipe=equipes_por_id[linha["equipe_id"]],
                status=StatusContratacao[linha["status"]],
                id_banco=linha["id"],
            )
            eventos_por_id[linha["evento_id"]]._contratacoes.append(contratacao)

        return usuarios, equipes

    def salvar(
        self,
        usuarios: Iterable[Usuario],
        equipes: Iterable[EquipeDivulgacao],
        eventos: Iterable[Evento],
    ) -> None:
        """Insere ou atualiza todo o estado dentro de uma única transação."""
        usuarios = tuple(usuarios)
        equipes = tuple(equipes)
        eventos = tuple(eventos)
        with self._conexao:
            for usuario in usuarios:
                self._salvar_usuario(usuario)
            for equipe in equipes:
                self._salvar_equipe(equipe)
            for evento in eventos:
                self._salvar_evento(evento)
            for evento in eventos:
                self._salvar_partes_evento(evento)

    def _salvar_usuario(self, usuario: Usuario) -> None:
        tipo = "organizador" if isinstance(usuario, Organizador) else "participante"
        valores = (
            usuario.nome,
            usuario.email,
            usuario.senha_hash,
            usuario.senha_salt,
            tipo,
        )
        if usuario.id_banco is None:
            cursor = self._conexao.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, senha_salt, tipo)
                VALUES (?, ?, ?, ?, ?)
                """,
                valores,
            )
            usuario.id_banco = cursor.lastrowid
        else:
            self._conexao.execute(
                """
                UPDATE usuarios
                SET nome = ?, email = ?, senha_hash = ?, senha_salt = ?, tipo = ?
                WHERE id = ?
                """,
                (*valores, usuario.id_banco),
            )

    def _salvar_equipe(self, equipe: EquipeDivulgacao) -> None:
        valores = (equipe.nome, equipe.servicos, equipe.preco)
        if equipe.id_banco is None:
            cursor = self._conexao.execute(
                "INSERT INTO equipes (nome, servicos, preco) VALUES (?, ?, ?)",
                valores,
            )
            object.__setattr__(equipe, "id_banco", cursor.lastrowid)
        else:
            self._conexao.execute(
                "UPDATE equipes SET nome = ?, servicos = ?, preco = ? WHERE id = ?",
                (*valores, equipe.id_banco),
            )

    def _salvar_evento(self, evento: Evento) -> None:
        valores = (
            evento.organizador.id_banco,
            evento.titulo,
            evento.descricao,
            evento.data_hora,
            evento.local,
            evento.categoria,
            evento.vagas,
            evento.status.name,
        )
        if evento.id_banco is None:
            cursor = self._conexao.execute(
                """
                INSERT INTO eventos (
                    organizador_id, titulo, descricao, data_hora, local,
                    categoria, vagas, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                valores,
            )
            evento.id_banco = cursor.lastrowid
        else:
            self._conexao.execute(
                """
                UPDATE eventos SET
                    organizador_id = ?, titulo = ?, descricao = ?, data_hora = ?,
                    local = ?, categoria = ?, vagas = ?, status = ?
                WHERE id = ?
                """,
                (*valores, evento.id_banco),
            )

    def _salvar_partes_evento(self, evento: Evento) -> None:
        for ordem, inscricao in enumerate(evento.inscricoes):
            valores = (
                evento.id_banco,
                inscricao.participante.id_banco,
                inscricao.status.name,
                ordem,
            )
            if inscricao.id_banco is None:
                cursor = self._conexao.execute(
                    """
                    INSERT INTO inscricoes (
                        evento_id, participante_id, status, ordem
                    ) VALUES (?, ?, ?, ?)
                    """,
                    valores,
                )
                inscricao.id_banco = cursor.lastrowid
            else:
                self._conexao.execute(
                    """
                    UPDATE inscricoes SET
                        evento_id = ?, participante_id = ?, status = ?, ordem = ?
                    WHERE id = ?
                    """,
                    (*valores, inscricao.id_banco),
                )

        for ordem, contratacao in enumerate(evento.contratacoes):
            valores = (
                evento.id_banco,
                contratacao.equipe.id_banco,
                contratacao.status.name,
                ordem,
            )
            if contratacao.id_banco is None:
                cursor = self._conexao.execute(
                    """
                    INSERT INTO contratacoes (evento_id, equipe_id, status, ordem)
                    VALUES (?, ?, ?, ?)
                    """,
                    valores,
                )
                contratacao.id_banco = cursor.lastrowid
            else:
                self._conexao.execute(
                    """
                    UPDATE contratacoes SET
                        evento_id = ?, equipe_id = ?, status = ?, ordem = ?
                    WHERE id = ?
                    """,
                    (*valores, contratacao.id_banco),
                )

    def resumo(self) -> dict[str, int]:
        """Retorna a quantidade de registros de cada tabela da aplicação."""
        return {
            tabela: self._conexao.execute(
                f"SELECT COUNT(*) FROM {tabela}"  # nome vem da constante TABELAS
            ).fetchone()[0]
            for tabela in self.TABELAS
        }

    def fechar(self) -> None:
        self._conexao.close()

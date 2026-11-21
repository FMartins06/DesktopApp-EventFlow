"""Modelo de domínio do EventFlow.

O módulo concentra as regras de negócio e evidencia relações de orientação a
objetos: herança, polimorfismo, composição, associação e dependência.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import secrets
from typing import Iterable


def interpretar_data_hora(valor: str) -> datetime:
    """Interpreta os formatos usados pelas interfaces do EventFlow."""
    for formato in ("%d/%m/%Y às %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(valor.strip(), formato)
        except ValueError:
            pass
    raise ValueError("Informe uma data e hora válidas, por exemplo 20/12/2026 às 18:00.")


class StatusEvento(Enum):
    RASCUNHO = "Rascunho"
    PUBLICADO = "Publicado"
    CANCELADO = "Cancelado"


class StatusInscricao(Enum):
    CONFIRMADA = "Confirmada"
    LISTA_ESPERA = "Lista de espera"
    CANCELADA = "Cancelada"


class StatusContratacao(Enum):
    ATIVA = "Ativa"
    CANCELADA = "Cancelada"


class Usuario(ABC):
    """Classe abstrata da qual os tipos de usuário herdam."""

    ITERACOES_HASH = 120_000

    def __init__(
        self,
        nome: str,
        email: str,
        senha: str | None,
        *,
        senha_hash: str | None = None,
        senha_salt: str | None = None,
        id_banco: int | None = None,
    ) -> None:
        if not nome.strip():
            raise ValueError("O nome é obrigatório.")
        if "@" not in email:
            raise ValueError("Informe um e-mail válido.")
        if senha_hash is None and not senha:
            raise ValueError("A senha é obrigatória.")
        if (senha_hash is None) != (senha_salt is None):
            raise ValueError("Hash e salt da senha devem ser informados juntos.")

        self.nome = nome.strip()
        self.email = email.strip().lower()
        self.id_banco = id_banco
        self.senha_salt = senha_salt or secrets.token_hex(16)
        self.senha_hash = senha_hash or self._gerar_hash(senha or "")

    def _gerar_hash(self, senha: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            bytes.fromhex(self.senha_salt),
            self.ITERACOES_HASH,
        ).hex()

    def verificar_senha(self, senha: str) -> bool:
        """Compara a senha sem armazená-la em texto puro."""
        return hmac.compare_digest(self.senha_hash, self._gerar_hash(senha))

    @abstractmethod
    def descricao_perfil(self) -> str:
        """Retorna uma descrição específica de cada subtipo de usuário."""


class Organizador(Usuario):
    def __init__(
        self,
        nome: str,
        email: str,
        senha: str | None,
        *,
        senha_hash: str | None = None,
        senha_salt: str | None = None,
        id_banco: int | None = None,
    ) -> None:
        super().__init__(
            nome,
            email,
            senha,
            senha_hash=senha_hash,
            senha_salt=senha_salt,
            id_banco=id_banco,
        )
        self._eventos: list[Evento] = []

    @property
    def eventos(self) -> tuple[Evento, ...]:
        return tuple(self._eventos)

    def descricao_perfil(self) -> str:
        return f"Organizador {self.nome}: cria e administra eventos"

    def criar_evento(
        self,
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
        *,
        _restaurar: bool = False,
    ) -> Evento:
        evento = Evento(
            titulo=titulo,
            descricao=descricao,
            data_hora=data_hora,
            local=local,
            categoria=categoria,
            vagas=vagas,
            organizador=self,
            _restaurar=_restaurar,
        )
        self._eventos.append(evento)
        return evento


class Participante(Usuario):
    def descricao_perfil(self) -> str:
        return f"Participante {self.nome}: demonstra interesse em eventos"


class GerenciadorUsuarios:
    """Mantém e autentica usuários que também podem existir fora dele."""

    def __init__(self) -> None:
        self._usuarios: list[Usuario] = []

    @property
    def usuarios(self) -> tuple[Usuario, ...]:
        return tuple(self._usuarios)

    def cadastrar(
        self,
        nome: str,
        email: str,
        senha: str,
        tipo: str,
    ) -> Usuario:
        email_normalizado = email.strip().lower()
        if any(usuario.email == email_normalizado for usuario in self._usuarios):
            raise ValueError("Já existe uma conta com esse e-mail.")

        tipos = {
            "organizador": Organizador,
            "participante": Participante,
        }
        classe_usuario = tipos.get(tipo.strip().lower())
        if classe_usuario is None:
            raise ValueError("O tipo deve ser organizador ou participante.")

        usuario = classe_usuario(nome, email_normalizado, senha)
        self._usuarios.append(usuario)
        return usuario

    def autenticar(self, email: str, senha: str) -> Usuario:
        email_normalizado = email.strip().lower()
        for usuario in self._usuarios:
            if usuario.email == email_normalizado and usuario.verificar_senha(senha):
                return usuario
        raise ValueError("E-mail ou senha incorretos.")

    def restaurar(
        self,
        id_banco: int,
        nome: str,
        email: str,
        tipo: str,
        senha_hash: str,
        senha_salt: str,
    ) -> Usuario:
        """Reconstrói um usuário persistido sem conhecer a senha original."""
        tipos = {
            "organizador": Organizador,
            "participante": Participante,
        }
        classe_usuario = tipos.get(tipo)
        if classe_usuario is None:
            raise ValueError(f"Tipo de usuário desconhecido no banco: {tipo}.")
        usuario = classe_usuario(
            nome,
            email,
            None,
            senha_hash=senha_hash,
            senha_salt=senha_salt,
            id_banco=id_banco,
        )
        self._usuarios.append(usuario)
        return usuario


@dataclass(frozen=True)
class EquipeDivulgacao:
    """Equipe independente que pode ser associada a várias contratações."""

    nome: str
    servicos: str
    preco: float
    id_banco: int | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not self.nome.strip() or not self.servicos.strip():
            raise ValueError("Nome e serviços da equipe são obrigatórios.")
        if self.preco < 0:
            raise ValueError("O preço da equipe não pode ser negativo.")


@dataclass
class Inscricao:
    """Parte composta do Evento, criada exclusivamente por ele."""

    participante: Participante
    status: StatusInscricao
    id_banco: int | None = field(default=None, compare=False)


@dataclass
class ContratacaoDivulgacao:
    """Parte composta do Evento, criada exclusivamente por ele."""

    equipe: EquipeDivulgacao
    status: StatusContratacao = StatusContratacao.ATIVA
    id_banco: int | None = field(default=None, compare=False)


class Evento:
    def __init__(
        self,
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
        organizador: Organizador,
        *,
        _restaurar: bool = False,
    ) -> None:
        self._validar_dados(
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
            validar_data=not _restaurar,
        )
        if not isinstance(organizador, Organizador):
            raise ValueError("O evento precisa ter um organizador.")

        self.titulo = titulo.strip()
        self.descricao = descricao.strip()
        self.data_hora = (data_hora.strip() if _restaurar else
                          interpretar_data_hora(data_hora).strftime("%d/%m/%Y às %H:%M"))
        self.local = local.strip()
        self.categoria = categoria.strip()
        self.vagas = vagas
        self.organizador = organizador
        self.id_banco: int | None = None
        self.status = StatusEvento.RASCUNHO
        self._inscricoes: list[Inscricao] = []
        self._contratacoes: list[ContratacaoDivulgacao] = []

    @staticmethod
    def _validar_dados(
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
        *,
        validar_data: bool = True,
    ) -> None:
        campos = [titulo, descricao, data_hora, local, categoria]
        if any(not campo.strip() for campo in campos):
            raise ValueError("Os dados textuais do evento são obrigatórios.")
        if validar_data:
            interpretar_data_hora(data_hora)
        if not isinstance(vagas, int) or isinstance(vagas, bool) or vagas < 1:
            raise ValueError("O evento precisa ter pelo menos uma vaga.")

    @property
    def inscricoes(self) -> tuple[Inscricao, ...]:
        return tuple(self._inscricoes)

    @property
    def contratacoes(self) -> tuple[ContratacaoDivulgacao, ...]:
        return tuple(self._contratacoes)

    @property
    def total_confirmados(self) -> int:
        return sum(
            inscricao.status == StatusInscricao.CONFIRMADA
            for inscricao in self._inscricoes
        )

    @property
    def vagas_disponiveis(self) -> int:
        return max(self.vagas - self.total_confirmados, 0)

    def _validar_responsavel(self, organizador: Organizador) -> None:
        if organizador is not self.organizador:
            raise PermissionError(
                "Somente o organizador responsável pode executar esta ação."
            )

    def publicar(self, organizador: Organizador) -> None:
        self._validar_responsavel(organizador)
        if self.status != StatusEvento.RASCUNHO:
            raise ValueError("Somente um evento em rascunho pode ser publicado.")
        self.status = StatusEvento.PUBLICADO

    def editar(
        self,
        organizador: Organizador,
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
    ) -> None:
        self._validar_responsavel(organizador)
        if self.status == StatusEvento.CANCELADO:
            raise ValueError("Um evento cancelado não pode ser editado.")
        self._validar_dados(
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
        )
        if vagas < self.total_confirmados:
            raise ValueError("As vagas não podem ser menores que os confirmados.")

        self.titulo = titulo.strip()
        self.descricao = descricao.strip()
        self.data_hora = interpretar_data_hora(data_hora).strftime("%d/%m/%Y às %H:%M")
        self.local = local.strip()
        self.categoria = categoria.strip()
        self.vagas = vagas
        self._promover_lista_espera()

    def _promover_lista_espera(self) -> None:
        vagas_livres = self.vagas_disponiveis
        for inscricao in self._inscricoes:
            if vagas_livres == 0:
                break
            if inscricao.status == StatusInscricao.LISTA_ESPERA:
                inscricao.status = StatusInscricao.CONFIRMADA
                vagas_livres -= 1

    def demonstrar_interesse(self, participante: Participante) -> Inscricao:
        if not isinstance(participante, Participante):
            raise TypeError("Somente participantes podem demonstrar interesse.")
        if self.status != StatusEvento.PUBLICADO:
            raise ValueError("O evento precisa estar publicado.")
        if any(
            inscricao.participante is participante
            and inscricao.status != StatusInscricao.CANCELADA
            for inscricao in self._inscricoes
        ):
            raise ValueError("O participante já possui uma inscrição ativa.")

        status = (
            StatusInscricao.CONFIRMADA
            if self.vagas_disponiveis > 0
            else StatusInscricao.LISTA_ESPERA
        )
        inscricao = Inscricao(participante, status)
        self._inscricoes.append(inscricao)
        return inscricao

    def cancelar_interesse(self, participante: Participante) -> Inscricao:
        inscricao = next(
            (
                item
                for item in self._inscricoes
                if item.participante is participante
                and item.status != StatusInscricao.CANCELADA
            ),
            None,
        )
        if inscricao is None:
            raise ValueError("O participante não possui uma inscrição ativa.")

        era_confirmada = inscricao.status == StatusInscricao.CONFIRMADA
        inscricao.status = StatusInscricao.CANCELADA

        if era_confirmada:
            self._promover_lista_espera()
        return inscricao

    def contratar_equipe(
        self,
        organizador: Organizador,
        equipe: EquipeDivulgacao,
    ) -> ContratacaoDivulgacao:
        self._validar_responsavel(organizador)
        if self.status != StatusEvento.PUBLICADO:
            raise ValueError("Só é possível contratar para um evento publicado.")
        if not isinstance(equipe, EquipeDivulgacao):
            raise TypeError("Informe uma equipe de divulgação válida.")
        if any(
            contratacao.equipe.nome.casefold() == equipe.nome.casefold()
            and contratacao.status == StatusContratacao.ATIVA
            for contratacao in self._contratacoes
        ):
            raise ValueError("Essa equipe já possui uma contratação ativa.")

        contratacao = ContratacaoDivulgacao(equipe)
        self._contratacoes.append(contratacao)
        return contratacao

    def cancelar_contratacao(
        self,
        organizador: Organizador,
        contratacao: ContratacaoDivulgacao,
    ) -> None:
        self._validar_responsavel(organizador)
        if contratacao not in self._contratacoes:
            raise ValueError("A contratação não pertence a este evento.")
        if contratacao.status != StatusContratacao.ATIVA:
            raise ValueError("A contratação já está cancelada.")
        contratacao.status = StatusContratacao.CANCELADA

    def substituir_equipe(
        self,
        organizador: Organizador,
        contratacao_atual: ContratacaoDivulgacao,
        nova_equipe: EquipeDivulgacao,
    ) -> ContratacaoDivulgacao:
        self._validar_responsavel(organizador)
        if contratacao_atual not in self._contratacoes:
            raise ValueError("A contratação não pertence a este evento.")
        if contratacao_atual.status != StatusContratacao.ATIVA:
            raise ValueError("A contratação atual não está ativa.")

        nova_contratacao = self.contratar_equipe(organizador, nova_equipe)
        contratacao_atual.status = StatusContratacao.CANCELADA
        return nova_contratacao

    def cancelar(self, organizador: Organizador) -> None:
        self._validar_responsavel(organizador)
        if self.status == StatusEvento.CANCELADO:
            raise ValueError("O evento já está cancelado.")

        self.status = StatusEvento.CANCELADO
        for inscricao in self._inscricoes:
            if inscricao.status != StatusInscricao.CANCELADA:
                inscricao.status = StatusInscricao.CANCELADA
        for contratacao in self._contratacoes:
            if contratacao.status == StatusContratacao.ATIVA:
                contratacao.status = StatusContratacao.CANCELADA


class RelatorioEventos:
    """Depende de Evento apenas durante a geração do relatório."""

    def gerar(self, eventos: Iterable[Evento]) -> str:
        linhas = ["RELATÓRIO DE EVENTOS"]
        for evento in eventos:
            linhas.append(
                f"- {evento.titulo} | {evento.status.value} | "
                f"confirmados: {evento.total_confirmados}/{evento.vagas}"
            )
        return "\n".join(linhas)


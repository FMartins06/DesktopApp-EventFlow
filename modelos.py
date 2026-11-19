"""Modelo de domínio do EventFlow para a entrega do Nível 1.

O módulo concentra as regras de negócio e evidencia relações de orientação a
objetos: herança, polimorfismo, composição, associação e dependência.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


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

    def __init__(self, nome: str, email: str, senha: str) -> None:
        if not nome.strip():
            raise ValueError("O nome é obrigatório.")
        if "@" not in email:
            raise ValueError("Informe um e-mail válido.")
        if not senha:
            raise ValueError("A senha é obrigatória.")

        self.nome = nome.strip()
        self.email = email.strip().lower()
        self.senha = senha

    @abstractmethod
    def descricao_perfil(self) -> str:
        """Retorna uma descrição específica de cada subtipo de usuário."""


class Organizador(Usuario):
    def __init__(self, nome: str, email: str, senha: str) -> None:
        super().__init__(nome, email, senha)
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
    ) -> Evento:
        evento = Evento(
            titulo=titulo,
            descricao=descricao,
            data_hora=data_hora,
            local=local,
            categoria=categoria,
            vagas=vagas,
            organizador=self,
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
            if usuario.email == email_normalizado and usuario.senha == senha:
                return usuario
        raise ValueError("E-mail ou senha incorretos.")


@dataclass(frozen=True)
class EquipeDivulgacao:
    """Equipe independente que pode ser associada a várias contratações."""

    nome: str
    servicos: str
    preco: float

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


@dataclass
class ContratacaoDivulgacao:
    """Parte composta do Evento, criada exclusivamente por ele."""

    equipe: EquipeDivulgacao
    status: StatusContratacao = StatusContratacao.ATIVA


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
    ) -> None:
        self._validar_dados(
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
        )
        if not isinstance(organizador, Organizador):
            raise ValueError("O evento precisa ter um organizador.")

        self.titulo = titulo.strip()
        self.descricao = descricao.strip()
        self.data_hora = data_hora.strip()
        self.local = local.strip()
        self.categoria = categoria.strip()
        self.vagas = vagas
        self.organizador = organizador
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
    ) -> None:
        campos = [titulo, descricao, data_hora, local, categoria]
        if any(not campo.strip() for campo in campos):
            raise ValueError("Os dados textuais do evento são obrigatórios.")
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
        self.data_hora = data_hora.strip()
        self.local = local.strip()
        self.categoria = categoria.strip()
        self.vagas = vagas

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
            proxima = next(
                (
                    item
                    for item in self._inscricoes
                    if item.status == StatusInscricao.LISTA_ESPERA
                ),
                None,
            )
            if proxima is not None:
                proxima.status = StatusInscricao.CONFIRMADA
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


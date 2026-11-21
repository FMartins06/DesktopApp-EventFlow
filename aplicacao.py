"""Camada de aplicação e menu de terminal do EventFlow.

Esta camada conecta os modelos de domínio à interface interativa e garante que
cada alteração seja persistida no banco SQLite.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from banco_dados import BancoDados

from modelos import (
    ContratacaoDivulgacao,
    EquipeDivulgacao,
    Evento,
    GerenciadorUsuarios,
    Inscricao,
    Organizador,
    Participante,
    RelatorioEventos,
    StatusContratacao,
    StatusEvento,
    StatusInscricao,
    Usuario,
)


CAMINHO_BANCO_PADRAO = Path(__file__).with_name("eventflow.db")


class SistemaEventFlow:
    """Coordena as regras de negócio e a persistência do estado."""

    def __init__(
        self,
        caminho_banco: str | Path = CAMINHO_BANCO_PADRAO,
    ) -> None:
        self.banco = BancoDados(caminho_banco)
        self.usuarios, self._equipes = self.banco.carregar()
        emails = {usuario.email for usuario in self.usuarios.usuarios}
        self._dados_demo_carregados = {
            "ana@eventflow.com",
            "bia@eventflow.com",
            "caio@eventflow.com",
        }.issubset(emails)

    @property
    def equipes(self) -> tuple[EquipeDivulgacao, ...]:
        return tuple(self._equipes)

    @property
    def eventos(self) -> tuple[Evento, ...]:
        eventos: list[Evento] = []
        for usuario in self.usuarios.usuarios:
            if isinstance(usuario, Organizador):
                eventos.extend(usuario.eventos)
        return tuple(eventos)

    @property
    def eventos_publicados(self) -> tuple[Evento, ...]:
        return tuple(
            evento
            for evento in self.eventos
            if evento.status == StatusEvento.PUBLICADO
        )

    def persistir(self) -> None:
        self.banco.salvar(self.usuarios.usuarios, self._equipes, self.eventos)

    def cadastrar_usuario(
        self,
        nome: str,
        email: str,
        senha: str,
        tipo: str,
    ) -> Usuario:
        usuario = self.usuarios.cadastrar(nome, email, senha, tipo)
        self.persistir()
        return usuario

    def criar_evento(
        self,
        organizador: Organizador,
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
    ) -> Evento:
        evento = organizador.criar_evento(
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
        )
        self.persistir()
        return evento

    def editar_evento(
        self,
        organizador: Organizador,
        evento: Evento,
        titulo: str,
        descricao: str,
        data_hora: str,
        local: str,
        categoria: str,
        vagas: int,
    ) -> None:
        evento.editar(
            organizador,
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
        )
        self.persistir()

    def publicar_evento(self, organizador: Organizador, evento: Evento) -> None:
        evento.publicar(organizador)
        self.persistir()

    def cancelar_evento(self, organizador: Organizador, evento: Evento) -> None:
        evento.cancelar(organizador)
        self.persistir()

    def cadastrar_equipe(
        self,
        nome: str,
        servicos: str,
        preco: float,
    ) -> EquipeDivulgacao:
        nome_normalizado = nome.strip().casefold()
        if any(
            equipe.nome.casefold() == nome_normalizado
            for equipe in self._equipes
        ):
            raise ValueError("Já existe uma equipe com esse nome.")
        equipe = EquipeDivulgacao(nome.strip(), servicos.strip(), preco)
        self._equipes.append(equipe)
        self.persistir()
        return equipe

    def contratar_equipe(
        self,
        organizador: Organizador,
        evento: Evento,
        equipe: EquipeDivulgacao,
    ) -> ContratacaoDivulgacao:
        contratacao = evento.contratar_equipe(organizador, equipe)
        self.persistir()
        return contratacao

    def cancelar_contratacao(
        self,
        organizador: Organizador,
        evento: Evento,
        contratacao: ContratacaoDivulgacao,
    ) -> None:
        evento.cancelar_contratacao(organizador, contratacao)
        self.persistir()

    def substituir_equipe(
        self,
        organizador: Organizador,
        evento: Evento,
        contratacao: ContratacaoDivulgacao,
        nova_equipe: EquipeDivulgacao,
    ) -> ContratacaoDivulgacao:
        nova = evento.substituir_equipe(organizador, contratacao, nova_equipe)
        self.persistir()
        return nova

    def demonstrar_interesse(
        self,
        evento: Evento,
        participante: Participante,
    ) -> Inscricao:
        inscricao = evento.demonstrar_interesse(participante)
        self.persistir()
        return inscricao

    def cancelar_interesse(
        self,
        evento: Evento,
        participante: Participante,
    ) -> Inscricao:
        inscricao = evento.cancelar_interesse(participante)
        self.persistir()
        return inscricao

    def inscricoes_de(
        self,
        participante: Participante,
    ) -> tuple[tuple[Evento, Inscricao], ...]:
        return tuple(
            (evento, inscricao)
            for evento in self.eventos
            for inscricao in evento.inscricoes
            if inscricao.participante is participante
        )

    def carregar_dados_demo(self) -> None:
        """Cria um cenário pequeno para agilizar uma demonstração do menu."""
        if self._dados_demo_carregados:
            raise ValueError("Os dados de demonstração já foram carregados.")

        emails_demo = {
            "ana@eventflow.com",
            "bia@eventflow.com",
            "caio@eventflow.com",
        }
        if any(usuario.email in emails_demo for usuario in self.usuarios.usuarios):
            raise ValueError(
                "Não foi possível carregar: um e-mail da demonstração já está em uso."
            )
        equipes_demo = {"mídia local", "alcance digital"}
        if any(equipe.nome.casefold() in equipes_demo for equipe in self._equipes):
            raise ValueError(
                "Não foi possível carregar: uma equipe da demonstração já existe."
            )

        ana = self.usuarios.cadastrar(
            "Ana",
            "ana@eventflow.com",
            "123",
            "organizador",
        )
        self.usuarios.cadastrar(
            "Bia",
            "bia@eventflow.com",
            "123",
            "participante",
        )
        self.usuarios.cadastrar(
            "Caio",
            "caio@eventflow.com",
            "123",
            "participante",
        )
        assert isinstance(ana, Organizador)

        evento = ana.criar_evento(
            titulo="Festival EventFlow",
            descricao="Música ao vivo e praça de alimentação.",
            data_hora="20/12/2026 às 18:00",
            local="Praça Central",
            categoria="Música",
            vagas=1,
        )
        evento.publicar(ana)
        self._equipes.append(
            EquipeDivulgacao(
                "Mídia Local",
                "Divulgação em rádio e imprensa regional",
                250.0,
            )
        )
        self._equipes.append(
            EquipeDivulgacao(
                "Alcance Digital",
                "Campanha em redes sociais",
                400.0,
            )
        )
        self._dados_demo_carregados = True
        self.persistir()

    def resumo_banco(self) -> dict[str, int]:
        return self.banco.resumo()


class MenuEventFlow:
    """Interface de texto navegável para todas as operações do domínio."""

    def __init__(
        self,
        sistema: SistemaEventFlow | None = None,
        entrada: Callable[[str], str] = input,
        saida: Callable[[str], None] = print,
    ) -> None:
        self.sistema = sistema or SistemaEventFlow()
        self._entrada = entrada
        self._saida = saida

    def executar(self) -> None:
        self._titulo("EVENTFLOW — DESK APP III")
        self._escrever(
            f"Banco SQLite ativo: {self.sistema.banco.caminho}\n"
            "Todas as alterações são salvas permanentemente."
        )

        try:
            while True:
                self._escrever(
                    "\nMENU PRINCIPAL\n"
                    "1 - Cadastrar usuário\n"
                    "2 - Entrar\n"
                    "3 - Ver eventos publicados\n"
                    "4 - Carregar dados de demonstração\n"
                    "5 - Ver resumo do banco de dados\n"
                    "0 - Sair"
                )
                opcao = self._ler_opcao(
                    "Escolha: ",
                    {"0", "1", "2", "3", "4", "5"},
                )

                if opcao == "0":
                    self._escrever("EventFlow encerrado. Até logo!")
                    return
                if opcao == "1":
                    self._proteger(self._cadastrar_usuario)
                elif opcao == "2":
                    self._proteger(self._entrar)
                elif opcao == "3":
                    self._listar_eventos_publicados()
                elif opcao == "4":
                    self._proteger(self._carregar_demo)
                else:
                    self._mostrar_resumo_banco()
        except (EOFError, KeyboardInterrupt):
            self._escrever("\nEventFlow encerrado.")

    def _cadastrar_usuario(self) -> None:
        self._titulo("CADASTRO DE USUÁRIO")
        nome = self._ler_obrigatorio("Nome: ")
        email = self._ler_obrigatorio("E-mail: ")
        senha = self._ler_obrigatorio("Senha: ")
        tipo_opcao = self._ler_opcao(
            "Tipo (1 - Organizador / 2 - Participante): ",
            {"1", "2"},
        )
        tipo = "organizador" if tipo_opcao == "1" else "participante"
        usuario = self.sistema.cadastrar_usuario(nome, email, senha, tipo)
        self._escrever(f"Usuário {usuario.nome} cadastrado como {tipo}.")

    def _entrar(self) -> None:
        self._titulo("LOGIN")
        email = self._ler_obrigatorio("E-mail: ")
        senha = self._ler_obrigatorio("Senha: ")
        usuario = self.sistema.usuarios.autenticar(email, senha)
        self._escrever(f"Bem-vindo(a), {usuario.nome}!")

        if isinstance(usuario, Organizador):
            self._menu_organizador(usuario)
        elif isinstance(usuario, Participante):
            self._menu_participante(usuario)

    def _carregar_demo(self) -> None:
        self.sistema.carregar_dados_demo()
        self._escrever(
            "Dados carregados. Contas: ana@eventflow.com, "
            "bia@eventflow.com e caio@eventflow.com; senha: 123."
        )

    def _mostrar_resumo_banco(self) -> None:
        self._titulo("BANCO DE DADOS SQLITE")
        self._escrever(f"Arquivo: {self.sistema.banco.caminho}")
        for tabela, quantidade in self.sistema.resumo_banco().items():
            self._escrever(f"{tabela}: {quantidade} registro(s)")

    def _menu_organizador(self, organizador: Organizador) -> None:
        while True:
            self._escrever(
                f"\nMENU DO ORGANIZADOR — {organizador.nome}\n"
                "1 - Ver meu perfil\n"
                "2 - Listar meus eventos\n"
                "3 - Criar evento\n"
                "4 - Gerenciar evento\n"
                "5 - Cadastrar equipe de divulgação\n"
                "6 - Listar equipes de divulgação\n"
                "7 - Gerar relatório dos meus eventos\n"
                "0 - Sair da conta"
            )
            opcao = self._ler_opcao(
                "Escolha: ",
                {"0", "1", "2", "3", "4", "5", "6", "7"},
            )

            if opcao == "0":
                self._escrever("Logout realizado.")
                return
            if opcao == "1":
                self._mostrar_perfil(organizador)
            elif opcao == "2":
                self._listar_eventos(organizador.eventos, "MEUS EVENTOS")
            elif opcao == "3":
                self._proteger(lambda: self._criar_evento(organizador))
            elif opcao == "4":
                self._proteger(
                    lambda: self._selecionar_evento_para_gerenciar(organizador)
                )
            elif opcao == "5":
                self._proteger(self._cadastrar_equipe)
            elif opcao == "6":
                self._listar_equipes()
            else:
                self._gerar_relatorio(organizador)

    def _criar_evento(self, organizador: Organizador) -> None:
        self._titulo("CRIAR EVENTO")
        evento = self.sistema.criar_evento(
            organizador=organizador,
            titulo=self._ler_obrigatorio("Título: "),
            descricao=self._ler_obrigatorio("Descrição: "),
            data_hora=self._ler_obrigatorio("Data e hora (ex.: 20/12/2026 às 18:00): "),
            local=self._ler_obrigatorio("Local: "),
            categoria=self._ler_obrigatorio("Categoria: "),
            vagas=self._ler_inteiro_positivo("Quantidade de vagas: "),
        )
        self._escrever(f"Evento '{evento.titulo}' criado como rascunho.")

    def _selecionar_evento_para_gerenciar(self, organizador: Organizador) -> None:
        evento = self._selecionar_evento(organizador.eventos, "ESCOLHA UM EVENTO")
        if evento is not None:
            self._menu_evento(organizador, evento)

    def _menu_evento(self, organizador: Organizador, evento: Evento) -> None:
        while True:
            self._mostrar_detalhes_evento(evento)
            self._escrever(
                "\nAÇÕES DO EVENTO\n"
                "1 - Editar\n"
                "2 - Publicar\n"
                "3 - Cancelar evento\n"
                "4 - Ver inscrições\n"
                "5 - Ver contratações\n"
                "6 - Contratar equipe\n"
                "7 - Cancelar contratação\n"
                "8 - Substituir equipe\n"
                "0 - Voltar"
            )
            opcao = self._ler_opcao(
                "Escolha: ",
                {"0", "1", "2", "3", "4", "5", "6", "7", "8"},
            )
            if opcao == "0":
                return
            if opcao == "1":
                self._proteger(lambda: self._editar_evento(organizador, evento))
            elif opcao == "2":
                self._proteger(lambda: self._publicar_evento(organizador, evento))
            elif opcao == "3":
                self._proteger(lambda: self._cancelar_evento(organizador, evento))
            elif opcao == "4":
                self._listar_inscricoes(evento)
            elif opcao == "5":
                self._listar_contratacoes(evento)
            elif opcao == "6":
                self._proteger(lambda: self._contratar_equipe(organizador, evento))
            elif opcao == "7":
                self._proteger(lambda: self._cancelar_contratacao(organizador, evento))
            else:
                self._proteger(lambda: self._substituir_equipe(organizador, evento))

    def _editar_evento(self, organizador: Organizador, evento: Evento) -> None:
        self._titulo("EDITAR EVENTO")
        self._escrever("Pressione Enter para manter o valor atual.")
        titulo = self._ler_com_padrao("Título", evento.titulo)
        descricao = self._ler_com_padrao("Descrição", evento.descricao)
        data_hora = self._ler_com_padrao("Data e hora", evento.data_hora)
        local = self._ler_com_padrao("Local", evento.local)
        categoria = self._ler_com_padrao("Categoria", evento.categoria)
        vagas = self._ler_inteiro_com_padrao("Vagas", evento.vagas)
        self.sistema.editar_evento(
            organizador,
            evento,
            titulo,
            descricao,
            data_hora,
            local,
            categoria,
            vagas,
        )
        self._escrever("Evento atualizado.")

    def _publicar_evento(self, organizador: Organizador, evento: Evento) -> None:
        self.sistema.publicar_evento(organizador, evento)
        self._escrever("Evento publicado e visível para os participantes.")

    def _cancelar_evento(self, organizador: Organizador, evento: Evento) -> None:
        if not self._confirmar("Cancelar o evento e suas operações ativas?"):
            self._escrever("Cancelamento não realizado.")
            return
        self.sistema.cancelar_evento(organizador, evento)
        self._escrever("Evento cancelado.")

    def _cadastrar_equipe(self) -> None:
        self._titulo("CADASTRAR EQUIPE DE DIVULGAÇÃO")
        equipe = self.sistema.cadastrar_equipe(
            nome=self._ler_obrigatorio("Nome: "),
            servicos=self._ler_obrigatorio("Serviços: "),
            preco=self._ler_decimal_nao_negativo("Preço: R$ "),
        )
        self._escrever(f"Equipe '{equipe.nome}' cadastrada.")

    def _contratar_equipe(self, organizador: Organizador, evento: Evento) -> None:
        equipe = self._selecionar_equipe()
        if equipe is None:
            return
        contratacao = self.sistema.contratar_equipe(organizador, evento, equipe)
        self._escrever(
            f"Equipe '{contratacao.equipe.nome}' contratada para o evento."
        )

    def _cancelar_contratacao(
        self,
        organizador: Organizador,
        evento: Evento,
    ) -> None:
        ativas = tuple(
            contratacao
            for contratacao in evento.contratacoes
            if contratacao.status == StatusContratacao.ATIVA
        )
        contratacao = self._selecionar_contratacao(ativas)
        if contratacao is None:
            return
        if not self._confirmar(f"Cancelar a contratação de {contratacao.equipe.nome}?"):
            self._escrever("Cancelamento não realizado.")
            return
        self.sistema.cancelar_contratacao(organizador, evento, contratacao)
        self._escrever("Contratação cancelada.")

    def _substituir_equipe(self, organizador: Organizador, evento: Evento) -> None:
        ativas = tuple(
            contratacao
            for contratacao in evento.contratacoes
            if contratacao.status == StatusContratacao.ATIVA
        )
        atual = self._selecionar_contratacao(ativas, "CONTRATAÇÃO A SUBSTITUIR")
        if atual is None:
            return
        nova_equipe = self._selecionar_equipe("NOVA EQUIPE")
        if nova_equipe is None:
            return
        nova = self.sistema.substituir_equipe(
            organizador,
            evento,
            atual,
            nova_equipe,
        )
        self._escrever(
            f"'{atual.equipe.nome}' foi substituída por '{nova.equipe.nome}'."
        )

    def _gerar_relatorio(self, organizador: Organizador) -> None:
        self._titulo("RELATÓRIO")
        self._escrever(RelatorioEventos().gerar(organizador.eventos))

    def _menu_participante(self, participante: Participante) -> None:
        while True:
            self._escrever(
                f"\nMENU DO PARTICIPANTE — {participante.nome}\n"
                "1 - Ver meu perfil\n"
                "2 - Listar eventos publicados\n"
                "3 - Ver evento e demonstrar interesse\n"
                "4 - Ver minhas inscrições\n"
                "5 - Cancelar interesse\n"
                "0 - Sair da conta"
            )
            opcao = self._ler_opcao(
                "Escolha: ",
                {"0", "1", "2", "3", "4", "5"},
            )

            if opcao == "0":
                self._escrever("Logout realizado.")
                return
            if opcao == "1":
                self._mostrar_perfil(participante)
            elif opcao == "2":
                self._listar_eventos_publicados()
            elif opcao == "3":
                self._proteger(lambda: self._demonstrar_interesse(participante))
            elif opcao == "4":
                self._listar_inscricoes_participante(participante)
            else:
                self._proteger(lambda: self._cancelar_interesse(participante))

    def _demonstrar_interesse(self, participante: Participante) -> None:
        evento = self._selecionar_evento(
            self.sistema.eventos_publicados,
            "EVENTOS PUBLICADOS",
        )
        if evento is None:
            return
        self._mostrar_detalhes_evento(evento)
        if not self._confirmar("Demonstrar interesse neste evento?"):
            self._escrever("Inscrição não realizada.")
            return
        inscricao = self.sistema.demonstrar_interesse(evento, participante)
        self._escrever(f"Interesse registrado: {inscricao.status.value}.")

    def _cancelar_interesse(self, participante: Participante) -> None:
        ativas = tuple(
            (evento, inscricao)
            for evento, inscricao in self.sistema.inscricoes_de(participante)
            if inscricao.status != StatusInscricao.CANCELADA
        )
        if not ativas:
            self._escrever("Você não possui inscrições ativas.")
            return

        self._titulo("INSCRIÇÕES ATIVAS")
        for indice, (evento, inscricao) in enumerate(ativas, start=1):
            self._escrever(
                f"{indice} - {evento.titulo} | {inscricao.status.value}"
            )
        indice = self._ler_indice(len(ativas))
        if indice is None:
            return
        evento, _ = ativas[indice]
        if not self._confirmar(f"Cancelar o interesse em '{evento.titulo}'?"):
            self._escrever("Cancelamento não realizado.")
            return
        self.sistema.cancelar_interesse(evento, participante)
        self._escrever("Interesse cancelado.")

    def _mostrar_perfil(self, usuario: Usuario) -> None:
        self._titulo("MEU PERFIL")
        self._escrever(usuario.descricao_perfil())
        self._escrever(f"E-mail: {usuario.email}")

    def _listar_eventos_publicados(self) -> None:
        self._listar_eventos(
            self.sistema.eventos_publicados,
            "EVENTOS PUBLICADOS",
        )

    def _listar_eventos(self, eventos: Sequence[Evento], titulo: str) -> None:
        self._titulo(titulo)
        if not eventos:
            self._escrever("Nenhum evento encontrado.")
            return
        for indice, evento in enumerate(eventos, start=1):
            self._escrever(
                f"{indice} - {evento.titulo} | {evento.status.value} | "
                f"{evento.data_hora} | {evento.local} | "
                f"vagas disponíveis: {evento.vagas_disponiveis}"
            )

    def _mostrar_detalhes_evento(self, evento: Evento) -> None:
        espera = sum(
            inscricao.status == StatusInscricao.LISTA_ESPERA
            for inscricao in evento.inscricoes
        )
        equipes_ativas = [
            contratacao.equipe.nome
            for contratacao in evento.contratacoes
            if contratacao.status == StatusContratacao.ATIVA
        ]
        self._titulo(evento.titulo.upper())
        self._escrever(f"Descrição: {evento.descricao}")
        self._escrever(f"Data e hora: {evento.data_hora}")
        self._escrever(f"Local: {evento.local}")
        self._escrever(f"Categoria: {evento.categoria}")
        self._escrever(f"Organizador: {evento.organizador.nome}")
        self._escrever(f"Status: {evento.status.value}")
        self._escrever(
            f"Confirmados: {evento.total_confirmados}/{evento.vagas} | "
            f"Lista de espera: {espera}"
        )
        self._escrever(
            "Equipes ativas: " + (", ".join(equipes_ativas) or "nenhuma")
        )

    def _listar_inscricoes(self, evento: Evento) -> None:
        self._titulo("INSCRIÇÕES")
        if not evento.inscricoes:
            self._escrever("O evento ainda não possui inscrições.")
            return
        for indice, inscricao in enumerate(evento.inscricoes, start=1):
            self._escrever(
                f"{indice} - {inscricao.participante.nome} "
                f"({inscricao.participante.email}) | {inscricao.status.value}"
            )

    def _listar_inscricoes_participante(self, participante: Participante) -> None:
        self._titulo("MINHAS INSCRIÇÕES")
        inscricoes = self.sistema.inscricoes_de(participante)
        if not inscricoes:
            self._escrever("Você ainda não demonstrou interesse em eventos.")
            return
        for indice, (evento, inscricao) in enumerate(inscricoes, start=1):
            self._escrever(
                f"{indice} - {evento.titulo} | {inscricao.status.value} | "
                f"evento: {evento.status.value}"
            )

    def _listar_equipes(self) -> None:
        self._titulo("EQUIPES DE DIVULGAÇÃO")
        if not self.sistema.equipes:
            self._escrever("Nenhuma equipe cadastrada.")
            return
        for indice, equipe in enumerate(self.sistema.equipes, start=1):
            self._escrever(
                f"{indice} - {equipe.nome} | {equipe.servicos} | "
                f"R$ {equipe.preco:.2f}"
            )

    def _listar_contratacoes(self, evento: Evento) -> None:
        self._titulo("CONTRATAÇÕES")
        if not evento.contratacoes:
            self._escrever("O evento ainda não possui contratações.")
            return
        for indice, contratacao in enumerate(evento.contratacoes, start=1):
            self._escrever(
                f"{indice} - {contratacao.equipe.nome} | "
                f"R$ {contratacao.equipe.preco:.2f} | {contratacao.status.value}"
            )

    def _selecionar_evento(
        self,
        eventos: Sequence[Evento],
        titulo: str,
    ) -> Evento | None:
        self._listar_eventos(eventos, titulo)
        if not eventos:
            return None
        indice = self._ler_indice(len(eventos))
        return None if indice is None else eventos[indice]

    def _selecionar_equipe(
        self,
        titulo: str = "ESCOLHA UMA EQUIPE",
    ) -> EquipeDivulgacao | None:
        equipes = self.sistema.equipes
        self._titulo(titulo)
        if not equipes:
            self._escrever("Nenhuma equipe cadastrada.")
            return None
        for indice, equipe in enumerate(equipes, start=1):
            self._escrever(
                f"{indice} - {equipe.nome} | {equipe.servicos} | "
                f"R$ {equipe.preco:.2f}"
            )
        indice = self._ler_indice(len(equipes))
        return None if indice is None else equipes[indice]

    def _selecionar_contratacao(
        self,
        contratacoes: Sequence[ContratacaoDivulgacao],
        titulo: str = "CONTRATAÇÕES ATIVAS",
    ) -> ContratacaoDivulgacao | None:
        self._titulo(titulo)
        if not contratacoes:
            self._escrever("Não há contratações ativas.")
            return None
        for indice, contratacao in enumerate(contratacoes, start=1):
            self._escrever(
                f"{indice} - {contratacao.equipe.nome} | "
                f"R$ {contratacao.equipe.preco:.2f}"
            )
        indice = self._ler_indice(len(contratacoes))
        return None if indice is None else contratacoes[indice]

    def _ler_indice(self, quantidade: int) -> int | None:
        while True:
            texto = self._entrada("Número (0 para voltar): ").strip()
            try:
                numero = int(texto)
            except ValueError:
                self._escrever("Digite um número inteiro.")
                continue
            if numero == 0:
                return None
            if 1 <= numero <= quantidade:
                return numero - 1
            self._escrever(f"Escolha um número entre 0 e {quantidade}.")

    def _ler_opcao(self, mensagem: str, validas: set[str]) -> str:
        while True:
            opcao = self._entrada(mensagem).strip()
            if opcao in validas:
                return opcao
            self._escrever("Opção inválida. Tente novamente.")

    def _ler_obrigatorio(self, mensagem: str) -> str:
        while True:
            valor = self._entrada(mensagem).strip()
            if valor:
                return valor
            self._escrever("Este campo é obrigatório.")

    def _ler_inteiro_positivo(self, mensagem: str) -> int:
        while True:
            texto = self._entrada(mensagem).strip()
            try:
                valor = int(texto)
            except ValueError:
                self._escrever("Digite um número inteiro.")
                continue
            if valor >= 1:
                return valor
            self._escrever("O valor deve ser pelo menos 1.")

    def _ler_decimal_nao_negativo(self, mensagem: str) -> float:
        while True:
            texto = self._entrada(mensagem).strip().replace(",", ".")
            try:
                valor = float(texto)
            except ValueError:
                self._escrever("Digite um valor numérico válido.")
                continue
            if valor >= 0:
                return valor
            self._escrever("O valor não pode ser negativo.")

    def _ler_com_padrao(self, rotulo: str, atual: str) -> str:
        valor = self._entrada(f"{rotulo} [{atual}]: ").strip()
        return valor or atual

    def _ler_inteiro_com_padrao(self, rotulo: str, atual: int) -> int:
        while True:
            texto = self._entrada(f"{rotulo} [{atual}]: ").strip()
            if not texto:
                return atual
            try:
                valor = int(texto)
            except ValueError:
                self._escrever("Digite um número inteiro.")
                continue
            if valor >= 1:
                return valor
            self._escrever("O valor deve ser pelo menos 1.")

    def _confirmar(self, mensagem: str) -> bool:
        resposta = self._ler_opcao(f"{mensagem} (s/n): ", {"s", "n", "S", "N"})
        return resposta.lower() == "s"

    def _proteger(self, acao: Callable[[], None]) -> None:
        try:
            acao()
        except (ValueError, TypeError, PermissionError) as erro:
            self._escrever(f"Não foi possível concluir: {erro}")

    def _titulo(self, texto: str) -> None:
        self._escrever(f"\n{'=' * 8} {texto} {'=' * 8}")

    def _escrever(self, texto: str) -> None:
        self._saida(texto)

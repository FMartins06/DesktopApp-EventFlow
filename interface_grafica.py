"""Interface desktop do EventFlow, construída com Tkinter e ttk."""

from __future__ import annotations

import math
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from aplicacao import SistemaEventFlow
from modelos import Organizador, Participante, RelatorioEventos, StatusEvento, StatusInscricao


FUNDO = "#f3f5fa"
BRANCO = "#ffffff"
TEXTO = "#19233d"
SUAVE = "#64718b"
AZUL = "#5454d4"
ESCURO = "#171d38"


class Formulario(tk.Toplevel):
    """Janela reutilizável para cadastro e edição de dados."""

    def __init__(self, pai, titulo, campos, salvar):
        super().__init__(pai)
        self.title(titulo)
        self.configure(bg=BRANCO)
        self.transient(pai)
        self.resizable(False, False)
        self.salvar = salvar
        self.entradas = {}
        corpo = tk.Frame(self, bg=BRANCO, padx=28, pady=24)
        corpo.pack(fill="both", expand=True)
        tk.Label(corpo, text=titulo, bg=BRANCO, fg=TEXTO,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 14))
        for chave, rotulo, valor, opcoes in campos:
            tk.Label(corpo, text=rotulo, bg=BRANCO, fg=TEXTO,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 3))
            if isinstance(opcoes, tuple):
                entrada = ttk.Combobox(corpo, values=opcoes, state="readonly", width=48)
                entrada.set(valor or opcoes[0])
            else:
                entrada = ttk.Entry(corpo, width=50, show="*" if opcoes == "senha" else "")
                entrada.insert(0, str(valor))
            entrada.pack(fill="x", ipady=4)
            self.entradas[chave] = entrada
        botoes = tk.Frame(corpo, bg=BRANCO)
        botoes.pack(fill="x", pady=(22, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botoes, text="Salvar", style="Accent.TButton",
                   command=self._enviar).pack(side="right", padx=8)
        self.bind("<Return>", lambda evento: self._enviar())
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        next(iter(self.entradas.values())).focus_set()

    def destroy(self):
        pai = self.master
        super().destroy()
        if isinstance(pai, tk.Toplevel) and pai.winfo_exists():
            pai.grab_set()

    def _enviar(self):
        valores = {chave: entrada.get().strip() for chave, entrada in self.entradas.items()}
        try:
            self.salvar(valores)
        except (ValueError, TypeError, PermissionError, sqlite3.Error) as erro:
            messagebox.showerror("Não foi possível concluir", str(erro), parent=self)
            return
        self.destroy()


class InterfaceEventFlow:
    def __init__(self, sistema=None, janela=None):
        self.sistema = sistema or SistemaEventFlow()
        self.janela = janela or tk.Tk()
        self.usuario = None
        self.pagina = "Início"
        self.janela.title("EventFlow | Gestão de eventos")
        self.janela.geometry("1180x740")
        self.janela.minsize(900, 600)
        self.janela.configure(bg=FUNDO)
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self._estilos()
        self._estrutura()
        self.mostrar_inicio()

    def _estilos(self):
        estilo = ttk.Style(self.janela)
        estilo.theme_use("clam")
        estilo.configure("TButton", font=("Segoe UI", 9), padding=(12, 8),
                         background="#e9ecf5", foreground=TEXTO, borderwidth=0)
        estilo.map("TButton", background=[("active", "#dce1f0")])
        estilo.configure("Accent.TButton", background=AZUL, foreground=BRANCO)
        estilo.map("Accent.TButton", background=[("active", "#4040b6")])
        estilo.configure("Treeview", rowheight=36, background=BRANCO,
                         fieldbackground=BRANCO, foreground=TEXTO, borderwidth=0,
                         font=("Segoe UI", 9))
        estilo.configure("Treeview.Heading", background="#e9ecf5", foreground=SUAVE,
                         font=("Segoe UI", 9, "bold"), relief="flat", padding=7)
        estilo.map("Treeview", background=[("selected", "#dcdfff")],
                   foreground=[("selected", TEXTO)])
        estilo.configure("TEntry", padding=5)
        estilo.configure("TCombobox", padding=5)

    def _estrutura(self):
        self.lateral = tk.Frame(self.janela, bg=ESCURO, width=220)
        self.lateral.pack(side="left", fill="y")
        self.lateral.pack_propagate(False)
        tk.Label(self.lateral, text="eventflow.", bg=ESCURO, fg=BRANCO,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=24, pady=(30, 0))
        tk.Label(self.lateral, text="GESTÃO DE EVENTOS", bg=ESCURO, fg="#929cb9",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=27, pady=(0, 32))
        self.menu = tk.Frame(self.lateral, bg=ESCURO)
        self.menu.pack(fill="x")
        self.rodape = tk.Label(self.lateral, text="Seus eventos em um só lugar.",
                               bg=ESCURO, fg="#929cb9", font=("Segoe UI", 8), wraplength=170)
        self.rodape.pack(side="bottom", anchor="w", padx=26, pady=26)
        self.area = tk.Frame(self.janela, bg=FUNDO)
        self.area.pack(side="left", fill="both", expand=True)
        self._menu()

    def _menu(self):
        for filho in self.menu.winfo_children():
            filho.destroy()
        itens = [("Início", self.mostrar_inicio), ("Explorar eventos", self.mostrar_eventos)]
        if isinstance(self.usuario, Organizador):
            itens += [("Meus eventos", self.meus_eventos), ("Equipes", self.mostrar_equipes),
                      ("Relatório", self.mostrar_relatorio)]
        elif isinstance(self.usuario, Participante):
            itens += [("Minhas inscrições", self.minhas_inscricoes)]
        if self.usuario:
            itens += [("Meu perfil", self.mostrar_perfil), ("Sair da conta", self.sair)]
        else:
            itens += [("Entrar", self.login), ("Criar conta", self.cadastro)]
        for texto, comando in itens:
            tk.Button(self.menu, text=texto, command=comando, anchor="w", relief="flat",
                      bd=0, padx=26, pady=11, font=("Segoe UI", 10),
                      bg="#30365b" if self.pagina == texto else ESCURO,
                      fg=BRANCO if self.pagina == texto else "#c4cbe1",
                      activebackground="#30365b", activeforeground=BRANCO,
                      cursor="hand2").pack(fill="x", pady=1)

    def _pagina(self, nome, descricao):
        self.pagina = nome
        self._menu()
        for filho in self.area.winfo_children():
            filho.destroy()
        cabecalho = tk.Frame(self.area, bg=FUNDO)
        cabecalho.pack(fill="x", padx=32, pady=(27, 15))
        tk.Label(cabecalho, text=nome, bg=FUNDO, fg=TEXTO,
                 font=("Segoe UI", 23, "bold")).pack(anchor="w")
        tk.Label(cabecalho, text=descricao, bg=FUNDO, fg=SUAVE,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        conteudo = tk.Frame(self.area, bg=FUNDO)
        conteudo.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        return conteudo

    def _botao(self, pai, texto, comando, destaque=False, lado="left"):
        botao = ttk.Button(pai, text=texto, command=comando,
                           style="Accent.TButton" if destaque else "TButton")
        botao.pack(side=lado, padx=(0, 8), pady=5)
        return botao

    def _tabela(self, pai, colunas, linhas):
        quadro = tk.Frame(pai, bg=BRANCO)
        quadro.pack(fill="both", expand=True, pady=(10, 0))
        tabela = ttk.Treeview(quadro, columns=[c[0] for c in colunas], show="headings",
                             selectmode="browse")
        for chave, titulo, largura in colunas:
            tabela.heading(chave, text=titulo)
            tabela.column(chave, width=largura, minwidth=60, stretch=True)
        barra = ttk.Scrollbar(quadro, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        for indice, linha in enumerate(linhas):
            tabela.insert("", "end", iid=str(indice), values=linha)
        return tabela

    def _selecionado(self, tabela, objetos):
        selecao = tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um item", "Selecione uma linha para continuar.", parent=tabela.winfo_toplevel())
            return None
        return objetos[int(selecao[0])]

    def _acao(self, acao, mensagem=None, atualizar=None, pai=None):
        try:
            resultado = acao()
        except (ValueError, TypeError, PermissionError, sqlite3.Error) as erro:
            messagebox.showerror("Não foi possível concluir", str(erro), parent=pai or self.janela)
            return None
        if atualizar:
            atualizar()
        if mensagem:
            messagebox.showinfo("EventFlow", mensagem, parent=pai or self.janela)
        return resultado

    def mostrar_inicio(self):
        nome = self.usuario.nome if self.usuario else "você"
        area = self._pagina("Início", f"Bem-vindo(a), {nome}. Planeje e acompanhe seus eventos.")
        destaque = tk.Frame(area, bg=AZUL, padx=28, pady=25)
        destaque.pack(fill="x", pady=(5, 22))
        tk.Label(destaque, text="Boas ideias merecem\ngrandes encontros.", justify="left",
                 bg=AZUL, fg=BRANCO, font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(destaque, text="Descubra eventos ou organize o próximo com o EventFlow.",
                 bg=AZUL, fg="#e4e5ff", font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 15))
        self._botao(destaque, "Explorar eventos", self.mostrar_eventos)
        cards = tk.Frame(area, bg=FUNDO)
        cards.pack(fill="x")
        numeros = [("Eventos publicados", len(self.sistema.eventos_publicados)),
                   ("Equipes cadastradas", len(self.sistema.equipes))]
        if isinstance(self.usuario, Organizador):
            numeros.append(("Meus eventos", len(self.usuario.eventos)))
        elif isinstance(self.usuario, Participante):
            numeros.append(("Minhas inscrições", len(self.sistema.inscricoes_de(self.usuario))))
        for titulo, valor in numeros:
            card = tk.Frame(cards, bg=BRANCO, padx=20, pady=16)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            tk.Label(card, text=titulo, bg=BRANCO, fg=SUAVE,
                     font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(card, text=str(valor), bg=BRANCO, fg=TEXTO,
                     font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ferramentas = tk.Frame(area, bg=FUNDO)
        ferramentas.pack(fill="x", pady=(22, 0))
        if not self.usuario:
            self._botao(ferramentas, "Entrar", self.login, True)
            self._botao(ferramentas, "Criar conta", self.cadastro)
        self._botao(ferramentas, "Carregar demonstração", self.carregar_demo)
        self._botao(ferramentas, "Resumo do banco", self.resumo_banco)

    def login(self):
        def salvar(dados):
            self.usuario = self.sistema.usuarios.autenticar(dados["email"], dados["senha"])
            self.mostrar_inicio()
        Formulario(self.janela, "Entrar na conta", [
            ("email", "E-mail", "", None), ("senha", "Senha", "", "senha")], salvar)

    def cadastro(self):
        def salvar(dados):
            tipo = "organizador" if dados["tipo"] == "Organizador" else "participante"
            self.usuario = self.sistema.cadastrar_usuario(dados["nome"], dados["email"], dados["senha"], tipo)
            self.mostrar_inicio()
        Formulario(self.janela, "Criar conta", [
            ("nome", "Nome", "", None), ("email", "E-mail", "", None),
            ("senha", "Senha", "", "senha"),
            ("tipo", "Perfil", "Participante", ("Participante", "Organizador"))], salvar)

    def sair(self):
        self.usuario = None
        self.mostrar_inicio()

    def carregar_demo(self):
        if messagebox.askyesno("Dados de demonstração", "Adicionar contas, equipes e um evento de exemplo?", parent=self.janela):
            self._acao(self.sistema.carregar_dados_demo, "Dados de demonstração carregados.\nSenha das contas: 123.", self.mostrar_inicio)

    def resumo_banco(self):
        resumo = self.sistema.resumo_banco()
        texto = "\n".join(f"{nome.capitalize()}: {quantidade}" for nome, quantidade in resumo.items())
        messagebox.showinfo("Resumo do banco de dados", texto, parent=self.janela)

    def mostrar_perfil(self):
        area = self._pagina("Meu perfil", "Informações da sua conta.")
        quadro = tk.Frame(area, bg=BRANCO, padx=24, pady=24)
        quadro.pack(fill="x", pady=10)
        for texto in (self.usuario.descricao_perfil(), f"E-mail: {self.usuario.email}"):
            tk.Label(quadro, text=texto, bg=BRANCO, fg=TEXTO,
                     font=("Segoe UI", 11)).pack(anchor="w", pady=5)

    def mostrar_eventos(self):
        self._lista_eventos(self.sistema.eventos_publicados, "Explorar eventos",
                             "Descubra eventos publicados e consulte seus detalhes.")

    def meus_eventos(self):
        self._lista_eventos(self.usuario.eventos, "Meus eventos",
                             "Crie, acompanhe e gerencie seus eventos.")

    def _lista_eventos(self, eventos, titulo, descricao):
        eventos = tuple(eventos)
        area = self._pagina(titulo, descricao)
        acoes = tk.Frame(area, bg=FUNDO)
        acoes.pack(fill="x")
        if titulo == "Meus eventos":
            self._botao(acoes, "+ Criar evento", self.criar_evento, True)
        tabela = self._tabela(area, [("titulo", "Evento", 180), ("data", "Data e hora", 155),
            ("local", "Local", 135), ("status", "Status", 95), ("vagas", "Vagas livres", 90)],
            [(e.titulo, e.data_hora, e.local, e.status.value, e.vagas_disponiveis) for e in eventos])
        def abrir():
            evento = self._selecionado(tabela, eventos)
            if evento is not None:
                self.detalhes_evento(evento, titulo == "Meus eventos")
        self._botao(acoes, "Ver detalhes" if titulo != "Meus eventos" else "Gerenciar evento", abrir)
        tabela.bind("<Double-1>", lambda evento: abrir())

    def criar_evento(self, evento=None, atualizar=None, pai=None):
        def valor(chave):
            return getattr(evento, chave) if evento else ""
        def salvar(dados):
            try:
                vagas = int(dados["vagas"])
            except ValueError:
                raise ValueError("Informe um número inteiro de vagas.") from None
            argumentos = (dados["titulo"], dados["descricao"], dados["data_hora"],
                          dados["local"], dados["categoria"], vagas)
            if evento:
                self.sistema.editar_evento(self.usuario, evento, *argumentos)
            else:
                self.sistema.criar_evento(self.usuario, *argumentos)
            if atualizar:
                atualizar()
            else:
                self.meus_eventos()
        Formulario(pai or self.janela, "Editar evento" if evento else "Criar evento", [
            ("titulo", "Título", valor("titulo"), None),
            ("descricao", "Descrição", valor("descricao"), None),
            ("data_hora", "Data e hora (ex.: 20/12/2026 às 18:00)", valor("data_hora"), None),
            ("local", "Local", valor("local"), None),
            ("categoria", "Categoria", valor("categoria"), None),
            ("vagas", "Número de vagas", valor("vagas"), None)], salvar)

    def detalhes_evento(self, evento, gerenciar=False):
        janela = tk.Toplevel(self.janela)
        janela.title("Evento | EventFlow")
        janela.geometry("850x650")
        janela.minsize(740, 540)
        janela.configure(bg=FUNDO)
        janela.transient(self.janela)
        janela.grab_set()
        def desenhar():
            for filho in janela.winfo_children():
                if not isinstance(filho, tk.Toplevel):
                    filho.destroy()
            corpo = tk.Frame(janela, bg=FUNDO, padx=25, pady=20)
            corpo.pack(fill="both", expand=True)
            tk.Label(corpo, text=evento.titulo, bg=FUNDO, fg=TEXTO,
                     font=("Segoe UI", 19, "bold")).pack(anchor="w")
            espera = sum(i.status == StatusInscricao.LISTA_ESPERA for i in evento.inscricoes)
            descricao = (f"{evento.status.value}  •  {evento.categoria}  •  {evento.data_hora}\n"
                         f"{evento.local}  |  Organizador: {evento.organizador.nome}\n"
                         f"{evento.descricao}\n"
                         f"Confirmados: {evento.total_confirmados}/{evento.vagas}  |  Lista de espera: {espera}")
            tk.Label(corpo, text=descricao, bg=FUNDO, fg=SUAVE, justify="left",
                     wraplength=760, font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 10))
            acoes = tk.Frame(corpo, bg=FUNDO)
            acoes.pack(fill="x")
            if gerenciar:
                if evento.status != StatusEvento.CANCELADO:
                    self._botao(acoes, "Editar", lambda: self.criar_evento(evento, desenhar, janela))
                    if evento.status == StatusEvento.RASCUNHO:
                        self._botao(acoes, "Publicar", lambda: self._acao(
                            lambda: self.sistema.publicar_evento(self.usuario, evento), "Evento publicado.", desenhar, janela), True)
                    self._botao(acoes, "Cancelar evento", lambda: cancelar_evento())
                abas = ttk.Notebook(corpo)
                abas.pack(fill="both", expand=True, pady=(10, 0))
                inscritos = tk.Frame(abas, bg=FUNDO, padx=8, pady=8)
                contratacoes = tk.Frame(abas, bg=FUNDO, padx=8, pady=8)
                abas.add(inscritos, text="Inscrições")
                abas.add(contratacoes, text="Equipes contratadas")
                self._tabela(inscritos, [("nome", "Participante", 180), ("email", "E-mail", 220),
                    ("status", "Situação", 120)],
                    [(i.participante.nome, i.participante.email, i.status.value) for i in evento.inscricoes])
                barra = tk.Frame(contratacoes, bg=FUNDO)
                barra.pack(fill="x")
                itens = evento.contratacoes
                tabela = self._tabela(contratacoes, [("nome", "Equipe", 180), ("preco", "Preço", 100),
                    ("status", "Situação", 100)],
                    [(c.equipe.nome, f"R$ {c.equipe.preco:.2f}", c.status.value) for c in itens])
                if evento.status == StatusEvento.PUBLICADO:
                    self._botao(barra, "Contratar equipe", lambda: self.escolher_equipe(janela, evento, desenhar))
                def selecionada():
                    return self._selecionado(tabela, itens)
                def cancelar_contratacao():
                    atual = selecionada()
                    if atual is not None and messagebox.askyesno("Cancelar contratação", "Cancelar esta contratação?", parent=janela):
                        self._acao(lambda: self.sistema.cancelar_contratacao(self.usuario, evento, atual),
                                   "Contratação cancelada.", desenhar, janela)
                def substituir():
                    atual = selecionada()
                    if atual is not None:
                        self.escolher_equipe(janela, evento, desenhar, atual)
                if evento.status != StatusEvento.CANCELADO:
                    self._botao(barra, "Substituir", substituir)
                    self._botao(barra, "Cancelar contratação", cancelar_contratacao)
            else:
                equipes = ", ".join(c.equipe.nome for c in evento.contratacoes if c.status.value == "Ativa") or "Nenhuma"
                tk.Label(corpo, text="Equipes de divulgação: " + equipes, bg=FUNDO, fg=TEXTO,
                         wraplength=760, justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=10)
                if isinstance(self.usuario, Participante):
                    def inscrever():
                        resultado = self._acao(lambda: self.sistema.demonstrar_interesse(evento, self.usuario),
                                               atualizar=desenhar, pai=janela)
                        if resultado is not None:
                            messagebox.showinfo("Inscrição realizada", f"Situação: {resultado.status.value}.", parent=janela)
                    self._botao(acoes, "Demonstrar interesse", inscrever, True)
                elif self.usuario is None:
                    tk.Label(corpo, text="Entre como participante para demonstrar interesse.", bg=FUNDO,
                             fg=SUAVE, font=("Segoe UI", 10)).pack(anchor="w")
        def cancelar_evento():
            if messagebox.askyesno("Cancelar evento", "Cancelar o evento e suas inscrições e contratações ativas?", parent=janela):
                self._acao(lambda: self.sistema.cancelar_evento(self.usuario, evento), "Evento cancelado.", desenhar, janela)
        def fechar():
            janela.destroy()
            if gerenciar:
                self.meus_eventos()
            else:
                self.mostrar_eventos()
        janela.protocol("WM_DELETE_WINDOW", fechar)
        desenhar()

    def escolher_equipe(self, pai, evento, atualizar, atual=None):
        equipes = self.sistema.equipes
        if not equipes:
            messagebox.showinfo("Equipes", "Cadastre uma equipe no menu Equipes primeiro.", parent=pai)
            return
        nomes = tuple(f"{i + 1} - {e.nome} | R$ {e.preco:.2f}" for i, e in enumerate(equipes))
        def salvar(dados):
            equipe = equipes[nomes.index(dados["equipe"])]
            if atual:
                self.sistema.substituir_equipe(self.usuario, evento, atual, equipe)
            else:
                self.sistema.contratar_equipe(self.usuario, evento, equipe)
            atualizar()
        Formulario(pai, "Substituir equipe" if atual else "Contratar equipe",
                   [("equipe", "Selecione a equipe", nomes[0], nomes)], salvar)

    def mostrar_equipes(self):
        area = self._pagina("Equipes", "Consulte e cadastre equipes de divulgação.")
        acoes = tk.Frame(area, bg=FUNDO)
        acoes.pack(fill="x")
        self._botao(acoes, "+ Cadastrar equipe", self.cadastrar_equipe, True)
        self._tabela(area, [("nome", "Equipe", 160), ("servicos", "Serviços", 300),
            ("preco", "Preço", 110)],
            [(e.nome, e.servicos, f"R$ {e.preco:.2f}") for e in self.sistema.equipes])

    def cadastrar_equipe(self):
        def salvar(dados):
            try:
                preco = float(dados["preco"].replace(",", "."))
            except ValueError:
                raise ValueError("Informe um preço numérico válido.") from None
            if not math.isfinite(preco):
                raise ValueError("Informe um preço numérico válido.")
            self.sistema.cadastrar_equipe(dados["nome"], dados["servicos"], preco)
            self.mostrar_equipes()
        Formulario(self.janela, "Cadastrar equipe", [("nome", "Nome", "", None),
            ("servicos", "Serviços oferecidos", "", None),
            ("preco", "Preço (R$)", "", None)], salvar)

    def minhas_inscricoes(self):
        inscricoes = self.sistema.inscricoes_de(self.usuario)
        area = self._pagina("Minhas inscrições", "Acompanhe ou cancele seu interesse em eventos.")
        acoes = tk.Frame(area, bg=FUNDO)
        acoes.pack(fill="x")
        tabela = self._tabela(area, [("evento", "Evento", 200), ("data", "Data e hora", 150),
            ("situacao", "Inscrição", 130), ("status", "Evento", 100)],
            [(e.titulo, e.data_hora, i.status.value, e.status.value) for e, i in inscricoes])
        def cancelar():
            item = self._selecionado(tabela, inscricoes)
            if item is None:
                return
            evento, inscricao = item
            if inscricao.status == StatusInscricao.CANCELADA:
                messagebox.showinfo("Inscrição", "Esta inscrição já está cancelada.", parent=self.janela)
                return
            if messagebox.askyesno("Cancelar interesse", f"Cancelar sua inscrição em '{evento.titulo}'?", parent=self.janela):
                self._acao(lambda: self.sistema.cancelar_interesse(evento, self.usuario),
                           "Interesse cancelado.", self.minhas_inscricoes)
        self._botao(acoes, "Cancelar interesse", cancelar)

    def mostrar_relatorio(self):
        area = self._pagina("Relatório", "Resumo dos eventos organizados por você.")
        quadro = tk.Frame(area, bg=BRANCO, padx=22, pady=22)
        quadro.pack(fill="both", expand=True, pady=10)
        texto = RelatorioEventos().gerar(self.usuario.eventos)
        tk.Label(quadro, text=texto, bg=BRANCO, fg=TEXTO, justify="left", anchor="nw",
                 font=("Segoe UI", 11)).pack(fill="both", expand=True)

    def fechar(self):
        self.sistema.banco.fechar()
        self.janela.destroy()

    def executar(self):
        self.janela.mainloop()

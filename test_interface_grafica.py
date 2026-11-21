"""Testes dos principais fluxos da interface com um banco temporário."""

import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from pathlib import Path
from unittest.mock import patch

from aplicacao import SistemaEventFlow
from interface_grafica import Formulario, InterfaceEventFlow
from modelos import StatusContratacao, StatusEvento, StatusInscricao


class TestInterfaceGrafica(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"Interface gráfica indisponível: {erro}")
        self.root.withdraw()
        self.temp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp.name) / "teste.db"
        self.app = InterfaceEventFlow(SistemaEventFlow(self.caminho), self.root)
        self.infos = patch("interface_grafica.messagebox.showinfo").start()
        self.erros = patch("interface_grafica.messagebox.showerror").start()
        patch("interface_grafica.messagebox.askyesno", return_value=True).start()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        self.app.fechar()
        self.temp.cleanup()

    def descendentes(self, janela):
        for filho in janela.winfo_children():
            yield filho
            yield from self.descendentes(filho)

    def botao(self, janela, texto):
        return next(w for w in self.descendentes(janela)
                    if isinstance(w, (tk.Button, ttk.Button)) and w.cget("text") == texto)

    def formulario(self):
        return next(w for w in self.descendentes(self.root) if isinstance(w, Formulario))

    def preencher(self, **valores):
        form = self.formulario()
        for chave, valor in valores.items():
            entrada = form.entradas[chave]
            if isinstance(entrada, ttk.Combobox):
                entrada.set(valor)
            else:
                entrada.delete(0, "end")
                entrada.insert(0, valor)
        form._enviar()
        self.assertFalse(form.winfo_exists(), "O formulário deveria ter sido salvo")
        self.erros.assert_not_called()

    def test_fluxo_grafico_evento_inscricoes_e_persistencia(self):
        self.app.cadastro()
        self.preencher(nome="Ana", email="ana@teste.com", senha="123", tipo="Organizador")
        self.app.criar_evento()
        self.preencher(titulo="Festival", descricao="Música", data_hora="20/12/2026 às 18:00",
                       local="Praça", categoria="Cultura", vagas="1")
        evento = self.app.sistema.eventos[0]
        self.app.meus_eventos()
        tabela = next(w for w in self.descendentes(self.root) if isinstance(w, ttk.Treeview))
        tabela.selection_set("0")
        self.botao(self.root, "Gerenciar evento").invoke()
        janela = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
        self.botao(janela, "Publicar").invoke()
        self.assertEqual(evento.status, StatusEvento.PUBLICADO)
        self.botao(janela, "Editar").invoke()
        self.preencher(titulo="Festival editado")
        self.assertEqual(evento.titulo, "Festival editado")
        janela.destroy()

        self.app.sair()
        for nome in ("Bia", "Caio"):
            self.app.cadastro()
            self.preencher(nome=nome, email=f"{nome.lower()}@teste.com", senha="123", tipo="Participante")
            self.app.mostrar_eventos()
            tabela = next(w for w in self.descendentes(self.root) if isinstance(w, ttk.Treeview))
            tabela.selection_set("0")
            self.botao(self.root, "Ver detalhes").invoke()
            janela = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
            self.botao(janela, "Demonstrar interesse").invoke()
            janela.destroy()
            self.app.sair()
        self.assertEqual([i.status for i in evento.inscricoes],
                         [StatusInscricao.CONFIRMADA, StatusInscricao.LISTA_ESPERA])
        self.app.login()
        self.preencher(email="bia@teste.com", senha="123")
        self.app.minhas_inscricoes()
        tabela = next(w for w in self.descendentes(self.root) if isinstance(w, ttk.Treeview))
        tabela.selection_set("0")
        self.botao(self.root, "Cancelar interesse").invoke()
        self.assertEqual(evento.inscricoes[1].status, StatusInscricao.CONFIRMADA)
        self.app.sistema.banco.fechar()
        self.app.sistema = SistemaEventFlow(self.caminho)
        restaurado = self.app.sistema.eventos[0]
        self.assertEqual([i.status for i in restaurado.inscricoes],
                         [StatusInscricao.CANCELADA, StatusInscricao.CONFIRMADA])

    def test_contratacao_substituicao_e_validacao(self):
        self.app.cadastro()
        self.preencher(nome="Ana", email="ana@teste.com", senha="123", tipo="Organizador")
        self.app.criar_evento()
        form = self.formulario()
        form._enviar()
        self.assertTrue(form.winfo_exists())
        self.erros.assert_called_once()
        self.erros.reset_mock()
        self.preencher(titulo="Festival", descricao="Música", data_hora="20/12/2026 às 18:00",
                       local="Praça", categoria="Cultura", vagas="3")
        for nome in ("Equipe A", "Equipe B"):
            self.app.cadastrar_equipe()
            self.preencher(nome=nome, servicos="Redes sociais", preco="250,00")
        evento = self.app.sistema.eventos[0]
        self.app.detalhes_evento(evento, True)
        janela = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
        self.botao(janela, "Publicar").invoke()
        self.botao(janela, "Contratar equipe").invoke()
        self.preencher(equipe="1 - Equipe A | R$ 250.00")
        tabela = list(w for w in self.descendentes(janela) if isinstance(w, ttk.Treeview))[1]
        tabela.selection_set("0")
        self.botao(janela, "Substituir").invoke()
        self.preencher(equipe="2 - Equipe B | R$ 250.00")
        self.assertEqual([c.status for c in evento.contratacoes],
                         [StatusContratacao.CANCELADA, StatusContratacao.ATIVA])
        tabela = list(w for w in self.descendentes(janela) if isinstance(w, ttk.Treeview))[1]
        tabela.selection_set("1")
        self.botao(janela, "Cancelar contratação").invoke()
        self.assertEqual(evento.contratacoes[1].status, StatusContratacao.CANCELADA)
        janela.destroy()

    def test_evento_cancelado_nao_exibe_acoes_indisponiveis(self):
        self.app.cadastro()
        self.preencher(nome="Ana", email="ana@teste.com", senha="123", tipo="Organizador")
        self.app.criar_evento()
        self.preencher(titulo="Festival", descricao="Música", data_hora="20/12/2026 às 18:00",
                       local="Praça", categoria="Cultura", vagas="1")
        evento = self.app.sistema.eventos[0]
        self.app.sistema.cancelar_evento(self.app.usuario, evento)
        self.app.detalhes_evento(evento, True)
        janela = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
        textos = [w.cget("text") for w in self.descendentes(janela) if isinstance(w, (tk.Button, ttk.Button))]
        for texto in ("Editar", "Publicar", "Cancelar evento", "Contratar equipe",
                      "Substituir", "Cancelar contratação"):
            self.assertNotIn(texto, textos)


if __name__ == "__main__":
    unittest.main()

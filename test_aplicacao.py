import unittest

from aplicacao import MenuEventFlow, SistemaEventFlow
from modelos import Organizador, Participante, StatusEvento, StatusInscricao


class TestSistemaEventFlow(unittest.TestCase):
    def test_reune_eventos_publicados_e_inscricoes_do_participante(self) -> None:
        sistema = SistemaEventFlow()
        organizador = sistema.usuarios.cadastrar(
            "Ana", "ana@email.com", "123", "organizador"
        )
        participante = sistema.usuarios.cadastrar(
            "Bia", "bia@email.com", "123", "participante"
        )
        self.assertIsInstance(organizador, Organizador)
        self.assertIsInstance(participante, Participante)

        evento = organizador.criar_evento(
            "Festival", "Música", "20/12/2026", "Praça", "Cultura", 10
        )
        self.assertEqual((), sistema.eventos_publicados)
        evento.publicar(organizador)
        inscricao = evento.demonstrar_interesse(participante)

        self.assertEqual((evento,), sistema.eventos)
        self.assertEqual((evento,), sistema.eventos_publicados)
        self.assertEqual(
            ((evento, inscricao),),
            sistema.inscricoes_de(participante),
        )

    def test_dados_demo_criam_usuarios_evento_e_equipes_uma_unica_vez(self) -> None:
        sistema = SistemaEventFlow()

        sistema.carregar_dados_demo()

        self.assertEqual(3, len(sistema.usuarios.usuarios))
        self.assertEqual(1, len(sistema.eventos))
        self.assertEqual(StatusEvento.PUBLICADO, sistema.eventos[0].status)
        self.assertEqual(2, len(sistema.equipes))
        with self.assertRaises(ValueError):
            sistema.carregar_dados_demo()

    def test_conflito_impede_carga_parcial_dos_dados_demo(self) -> None:
        sistema = SistemaEventFlow()
        sistema.cadastrar_equipe("Mídia Local", "Rádio", 100)

        with self.assertRaises(ValueError):
            sistema.carregar_dados_demo()

        self.assertEqual(0, len(sistema.usuarios.usuarios))
        self.assertEqual(0, len(sistema.eventos))
        self.assertEqual(1, len(sistema.equipes))

    def test_impede_equipes_com_nomes_duplicados(self) -> None:
        sistema = SistemaEventFlow()
        sistema.cadastrar_equipe("Mídia Local", "Rádio", 100)

        with self.assertRaises(ValueError):
            sistema.cadastrar_equipe("mídia local", "Internet", 200)


class TestMenuEventFlow(unittest.TestCase):
    def test_fluxo_completo_pelo_menu(self) -> None:
        entradas = iter(
            [
                # Cadastro do organizador.
                "1",
                "Ana",
                "ana@email.com",
                "123",
                "1",
                # Cadastro do participante.
                "1",
                "Bia",
                "bia@email.com",
                "123",
                "2",
                # Login do organizador e criação do evento.
                "2",
                "ana@email.com",
                "123",
                "3",
                "Festival",
                "Música ao vivo",
                "20/12/2026 às 18:00",
                "Praça Central",
                "Cultura",
                "1",
                # Publicação do evento.
                "4",
                "1",
                "2",
                "0",
                # Cadastro e contratação da equipe.
                "5",
                "Mídia Local",
                "Rádio e internet",
                "250,00",
                "4",
                "1",
                "6",
                "1",
                "0",
                # Logout e login do participante.
                "0",
                "2",
                "bia@email.com",
                "123",
                # Inscrição, consulta e cancelamento.
                "3",
                "1",
                "s",
                "4",
                "5",
                "1",
                "s",
                "0",
                "0",
            ]
        )
        saidas: list[str] = []
        sistema = SistemaEventFlow()
        menu = MenuEventFlow(
            sistema=sistema,
            entrada=lambda _: next(entradas),
            saida=saidas.append,
        )

        menu.executar()

        texto = "\n".join(saidas)
        self.assertIn("Evento 'Festival' criado como rascunho.", texto)
        self.assertIn("Evento publicado e visível", texto)
        self.assertIn("Equipe 'Mídia Local' contratada", texto)
        self.assertIn("Interesse registrado: Confirmada.", texto)
        self.assertIn("Interesse cancelado.", texto)
        self.assertIn("EventFlow encerrado", texto)
        self.assertEqual(
            StatusInscricao.CANCELADA,
            sistema.eventos[0].inscricoes[0].status,
        )

    def test_opcao_invalida_e_login_incorreto_nao_encerram_menu(self) -> None:
        entradas = iter(["9", "2", "ninguem@email.com", "errada", "0"])
        saidas: list[str] = []
        menu = MenuEventFlow(
            entrada=lambda _: next(entradas),
            saida=saidas.append,
        )

        menu.executar()

        texto = "\n".join(saidas)
        self.assertIn("Opção inválida", texto)
        self.assertIn("E-mail ou senha incorretos", texto)
        self.assertIn("EventFlow encerrado", texto)


if __name__ == "__main__":
    unittest.main()

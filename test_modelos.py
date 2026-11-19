import unittest

from modelos import (
    ContratacaoDivulgacao,
    EquipeDivulgacao,
    GerenciadorUsuarios,
    Organizador,
    Participante,
    RelatorioEventos,
    StatusContratacao,
    StatusEvento,
    StatusInscricao,
)


class TestUsuarios(unittest.TestCase):
    def setUp(self) -> None:
        self.gerenciador = GerenciadorUsuarios()

    def test_cadastra_subtipos_e_autentica_email_sem_diferenciar_maiusculas(self) -> None:
        organizador = self.gerenciador.cadastrar(
            "Ana", "ANA@email.com", "123", "organizador"
        )
        participante = self.gerenciador.cadastrar(
            "Bia", "bia@email.com", "abc", "participante"
        )

        self.assertIsInstance(organizador, Organizador)
        self.assertIsInstance(participante, Participante)
        self.assertIs(
            organizador,
            self.gerenciador.autenticar("ana@EMAIL.com", "123"),
        )

    def test_impede_email_duplicado_e_login_invalido(self) -> None:
        self.gerenciador.cadastrar("Ana", "ana@email.com", "123", "organizador")

        with self.assertRaises(ValueError):
            self.gerenciador.cadastrar(
                "Outra Ana", "ANA@email.com", "456", "participante"
            )
        with self.assertRaises(ValueError):
            self.gerenciador.autenticar("ana@email.com", "errada")

    def test_polimorfismo_retorna_descricoes_especificas(self) -> None:
        usuarios = [
            Organizador("Ana", "ana@email.com", "123"),
            Participante("Bia", "bia@email.com", "123"),
        ]

        descricoes = [usuario.descricao_perfil() for usuario in usuarios]

        self.assertIn("cria e administra eventos", descricoes[0])
        self.assertIn("demonstra interesse", descricoes[1])


class TestEvento(unittest.TestCase):
    def setUp(self) -> None:
        self.organizador = Organizador("Ana", "ana@email.com", "123")
        self.outro_organizador = Organizador("Davi", "davi@email.com", "123")
        self.bia = Participante("Bia", "bia@email.com", "123")
        self.caio = Participante("Caio", "caio@email.com", "123")
        self.evento = self.organizador.criar_evento(
            "Festival",
            "Música ao vivo",
            "20/12/2026 às 18:00",
            "Praça Central",
            "Música",
            1,
        )
        self.equipe_a = EquipeDivulgacao("Mídia Local", "Rádio", 250.0)
        self.equipe_b = EquipeDivulgacao("Alcance Digital", "Internet", 400.0)

    def publicar(self) -> None:
        self.evento.publicar(self.organizador)

    def test_organizador_fica_associado_ao_evento_criado(self) -> None:
        self.assertIs(self.evento.organizador, self.organizador)
        self.assertIn(self.evento, self.organizador.eventos)
        self.assertEqual(StatusEvento.RASCUNHO, self.evento.status)

    def test_edita_e_publica_evento(self) -> None:
        self.evento.editar(
            self.organizador,
            "Festival EventFlow",
            "Música e gastronomia",
            "21/12/2026 às 18:00",
            "Parque Central",
            "Cultura",
            2,
        )
        self.evento.publicar(self.organizador)

        self.assertEqual("Festival EventFlow", self.evento.titulo)
        self.assertEqual(2, self.evento.vagas)
        self.assertEqual(StatusEvento.PUBLICADO, self.evento.status)

    def test_bloqueia_acoes_do_organizador_errado(self) -> None:
        with self.assertRaises(PermissionError):
            self.evento.publicar(self.outro_organizador)

    def test_cria_confirmacao_e_lista_de_espera_por_composicao(self) -> None:
        self.publicar()

        primeira = self.evento.demonstrar_interesse(self.bia)
        segunda = self.evento.demonstrar_interesse(self.caio)

        self.assertEqual(StatusInscricao.CONFIRMADA, primeira.status)
        self.assertEqual(StatusInscricao.LISTA_ESPERA, segunda.status)
        self.assertEqual((primeira, segunda), self.evento.inscricoes)
        self.assertEqual(0, self.evento.vagas_disponiveis)

    def test_impede_interesse_duplicado_ou_em_evento_nao_publicado(self) -> None:
        with self.assertRaises(ValueError):
            self.evento.demonstrar_interesse(self.bia)

        self.publicar()
        self.evento.demonstrar_interesse(self.bia)
        with self.assertRaises(ValueError):
            self.evento.demonstrar_interesse(self.bia)

    def test_cancelar_interesse_promove_primeiro_da_lista(self) -> None:
        self.publicar()
        primeira = self.evento.demonstrar_interesse(self.bia)
        segunda = self.evento.demonstrar_interesse(self.caio)

        self.evento.cancelar_interesse(self.bia)

        self.assertEqual(StatusInscricao.CANCELADA, primeira.status)
        self.assertEqual(StatusInscricao.CONFIRMADA, segunda.status)

    def test_contrata_equipe_por_composicao_e_impede_duplicidade(self) -> None:
        self.publicar()
        contratacao = self.evento.contratar_equipe(self.organizador, self.equipe_a)

        self.assertIsInstance(contratacao, ContratacaoDivulgacao)
        self.assertIs(contratacao.equipe, self.equipe_a)
        self.assertIn(contratacao, self.evento.contratacoes)
        with self.assertRaises(ValueError):
            self.evento.contratar_equipe(self.organizador, self.equipe_a)

    def test_cancela_contratacao(self) -> None:
        self.publicar()
        contratacao = self.evento.contratar_equipe(self.organizador, self.equipe_a)

        self.evento.cancelar_contratacao(self.organizador, contratacao)

        self.assertEqual(StatusContratacao.CANCELADA, contratacao.status)

    def test_substitui_equipe(self) -> None:
        self.publicar()
        anterior = self.evento.contratar_equipe(self.organizador, self.equipe_a)

        nova = self.evento.substituir_equipe(
            self.organizador,
            anterior,
            self.equipe_b,
        )

        self.assertEqual(StatusContratacao.CANCELADA, anterior.status)
        self.assertEqual(StatusContratacao.ATIVA, nova.status)
        self.assertIs(self.equipe_b, nova.equipe)

    def test_cancelar_evento_cancela_partes_compostas_ativas(self) -> None:
        self.publicar()
        inscricao = self.evento.demonstrar_interesse(self.bia)
        contratacao = self.evento.contratar_equipe(self.organizador, self.equipe_a)

        self.evento.cancelar(self.organizador)

        self.assertEqual(StatusEvento.CANCELADO, self.evento.status)
        self.assertEqual(StatusInscricao.CANCELADA, inscricao.status)
        self.assertEqual(StatusContratacao.CANCELADA, contratacao.status)

    def test_nao_reduz_vagas_abaixo_dos_confirmados(self) -> None:
        self.evento.editar(
            self.organizador,
            self.evento.titulo,
            self.evento.descricao,
            self.evento.data_hora,
            self.evento.local,
            self.evento.categoria,
            2,
        )
        self.publicar()
        self.evento.demonstrar_interesse(self.bia)
        self.evento.demonstrar_interesse(self.caio)

        with self.assertRaises(ValueError):
            self.evento.editar(
                self.organizador,
                self.evento.titulo,
                self.evento.descricao,
                self.evento.data_hora,
                self.evento.local,
                self.evento.categoria,
                1,
            )


class TestRelatorioEventos(unittest.TestCase):
    def test_relatorio_depende_dos_eventos_recebidos_sem_armazena_los(self) -> None:
        organizador = Organizador("Ana", "ana@email.com", "123")
        evento = organizador.criar_evento(
            "Festival", "Música", "20/12/2026", "Praça", "Cultura", 10
        )
        evento.publicar(organizador)

        texto = RelatorioEventos().gerar([evento])

        self.assertIn("Festival | Publicado", texto)
        self.assertIn("confirmados: 0/10", texto)


if __name__ == "__main__":
    unittest.main()


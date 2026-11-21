import sqlite3
import tempfile
import unittest
from pathlib import Path

from aplicacao import SistemaEventFlow
from modelos import (
    Organizador,
    Participante,
    StatusContratacao,
    StatusEvento,
    StatusInscricao,
)


class TestPersistenciaSQLite(unittest.TestCase):
    def test_aumento_de_vagas_salva_promocao_na_reabertura(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste.db"
            sistema = SistemaEventFlow(caminho)
            org = sistema.cadastrar_usuario("Ana", "ana@teste.com", "123", "organizador")
            bia = sistema.cadastrar_usuario("Bia", "bia@teste.com", "123", "participante")
            caio = sistema.cadastrar_usuario("Caio", "caio@teste.com", "123", "participante")
            evento = sistema.criar_evento(org, "Evento", "Descrição", "20/12/2026 às 18:00", "Praça", "Cultura", 1)
            sistema.publicar_evento(org, evento)
            sistema.demonstrar_interesse(evento, bia)
            sistema.demonstrar_interesse(evento, caio)
            sistema.editar_evento(org, evento, evento.titulo, evento.descricao, evento.data_hora,
                                  evento.local, evento.categoria, 2)
            sistema.banco.fechar()
            reaberto = SistemaEventFlow(caminho)
            try:
                self.assertEqual([StatusInscricao.CONFIRMADA, StatusInscricao.CONFIRMADA],
                                 [i.status for i in reaberto.eventos[0].inscricoes])
            finally:
                reaberto.banco.fechar()

    def test_reabre_evento_com_data_antiga_e_exige_correcao_ao_editar(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste.db"
            sistema = SistemaEventFlow(caminho)
            org = sistema.cadastrar_usuario("Ana", "ana@teste.com", "123", "organizador")
            sistema.criar_evento(org, "Evento", "Descrição", "20/12/2026 às 18:00", "Praça", "Cultura", 1)
            sistema.banco._conexao.execute("UPDATE eventos SET data_hora = ?", ("20/12 às 18h",))
            sistema.banco._conexao.commit()
            sistema.banco.fechar()
            reaberto = SistemaEventFlow(caminho)
            try:
                evento = reaberto.eventos[0]
                self.assertEqual("20/12 às 18h", evento.data_hora)
                with self.assertRaises(ValueError):
                    reaberto.editar_evento(evento.organizador, evento, evento.titulo, evento.descricao,
                                           evento.data_hora, evento.local, evento.categoria, 1)
                reaberto.editar_evento(evento.organizador, evento, evento.titulo, evento.descricao,
                                       "2026-12-20T18:00", evento.local, evento.categoria, 1)
                self.assertEqual("20/12/2026 às 18:00", evento.data_hora)
            finally:
                reaberto.banco.fechar()

    def test_dados_completos_continuam_apos_fechar_e_reabrir(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste_eventflow.db"
            sistema = SistemaEventFlow(caminho)
            ana = sistema.cadastrar_usuario(
                "Ana", "ana@email.com", "senha-segura", "organizador"
            )
            bia = sistema.cadastrar_usuario(
                "Bia", "bia@email.com", "123", "participante"
            )
            caio = sistema.cadastrar_usuario(
                "Caio", "caio@email.com", "456", "participante"
            )
            self.assertIsInstance(ana, Organizador)
            self.assertIsInstance(bia, Participante)
            self.assertIsInstance(caio, Participante)

            evento = sistema.criar_evento(
                ana,
                "Festival",
                "Música ao vivo",
                "20/12/2026 às 18:00",
                "Praça Central",
                "Cultura",
                1,
            )
            sistema.publicar_evento(ana, evento)
            inscricao_bia = sistema.demonstrar_interesse(evento, bia)
            inscricao_caio = sistema.demonstrar_interesse(evento, caio)
            equipe = sistema.cadastrar_equipe("Mídia Local", "Rádio", 250.0)
            contratacao = sistema.contratar_equipe(ana, evento, equipe)
            sistema.cancelar_interesse(evento, bia)

            self.assertEqual(StatusInscricao.CANCELADA, inscricao_bia.status)
            self.assertEqual(StatusInscricao.CONFIRMADA, inscricao_caio.status)
            self.assertEqual(StatusContratacao.ATIVA, contratacao.status)
            sistema.banco.fechar()

            reaberto = SistemaEventFlow(caminho)
            organizador = reaberto.usuarios.autenticar(
                "ANA@EMAIL.COM", "senha-segura"
            )
            participante = reaberto.usuarios.autenticar("caio@email.com", "456")
            evento_restaurado = reaberto.eventos[0]

            self.assertIsInstance(organizador, Organizador)
            self.assertIsInstance(participante, Participante)
            self.assertEqual(StatusEvento.PUBLICADO, evento_restaurado.status)
            self.assertEqual(2, len(evento_restaurado.inscricoes))
            self.assertEqual(
                [StatusInscricao.CANCELADA, StatusInscricao.CONFIRMADA],
                [item.status for item in evento_restaurado.inscricoes],
            )
            self.assertEqual(
                StatusContratacao.ATIVA,
                evento_restaurado.contratacoes[0].status,
            )
            self.assertEqual(
                {
                    "usuarios": 3,
                    "eventos": 1,
                    "equipes": 1,
                    "inscricoes": 2,
                    "contratacoes": 1,
                },
                reaberto.resumo_banco(),
            )
            reaberto.banco.fechar()

            conexao = sqlite3.connect(caminho)
            try:
                senha_armazenada = conexao.execute(
                    "SELECT senha_hash FROM usuarios WHERE email = ?",
                    ("ana@email.com",),
                ).fetchone()[0]
            finally:
                conexao.close()
            self.assertNotEqual("senha-segura", senha_armazenada)

    def test_esquema_ativa_chaves_estrangeiras(self) -> None:
        sistema = SistemaEventFlow(":memory:")
        self.addCleanup(sistema.banco.fechar)

        chaves_ativas = sistema.banco._conexao.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        self.assertEqual(1, chaves_ativas)
        self.assertEqual(
            {"usuarios", "eventos", "equipes", "inscricoes", "contratacoes"},
            set(sistema.resumo_banco()),
        )


if __name__ == "__main__":
    unittest.main()

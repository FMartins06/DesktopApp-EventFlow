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

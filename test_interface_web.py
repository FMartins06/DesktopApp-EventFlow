"""Exercita a ponte HTML/Python e as requisições sem depender de rede."""

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from aplicacao import SistemaEventFlow
from interface_web import AplicacaoWeb, Requisicoes, acompanhar_interface


class TestInterfaceWeb(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp.name) / "eventflow.db"
        self.sistema = SistemaEventFlow(self.caminho)
        self.app = AplicacaoWeb(self.sistema)

    def tearDown(self):
        self.sistema.banco.fechar()
        self.temp.cleanup()

    def test_jornada_completa_e_reabertura(self):
        self.app.executar("cadastro", {"nome": "Ana", "email": "ana@teste.com", "senha": "123", "tipo": "organizador"})
        self.app.executar("criar_evento", {"titulo": "Festival", "descricao": "Música", "data_hora": "2026-12-20T18:00", "local": "Praça", "categoria": "Cultura", "vagas": "1"})
        evento = self.app.estado()["meus_eventos"][0]["id"]
        self.app.executar("editar_evento", {"evento_id": evento, "titulo": "Festival editado", "descricao": "Música", "data_hora": "2026-12-20T18:00", "local": "Praça", "categoria": "Cultura", "vagas": "1"})
        self.app.executar("publicar_evento", {"evento_id": evento})
        self.app.executar("cadastrar_equipe", {"nome": "Equipe A", "servicos": "Rádio", "preco": "200,00"})
        self.app.executar("cadastrar_equipe", {"nome": "Equipe B", "servicos": "Redes", "preco": "300"})
        equipe_a, equipe_b = [e["id"] for e in self.app.estado()["equipes"]]
        self.app.executar("contratar", {"evento_id": evento, "equipe_id": equipe_a})
        contrato = self.app.estado()["meus_eventos"][0]["contratacoes"][0]["id"]
        self.app.executar("substituir", {"evento_id": evento, "equipe_id": equipe_b, "contratacao_id": contrato})
        self.assertEqual([c["status"] for c in self.app.estado()["meus_eventos"][0]["contratacoes"]], ["Cancelada", "Ativa"])
        self.app.executar("sair", {})
        for nome in ("Bia", "Caio"):
            self.app.executar("cadastro", {"nome": nome, "email": f"{nome.lower()}@teste.com", "senha": "123", "tipo": "participante"})
            resultado = self.app.executar("inscrever", {"evento_id": evento})
            self.assertEqual(resultado["status"], "Confirmada" if nome == "Bia" else "Lista de espera")
            self.app.executar("sair", {})
        self.app.executar("login", {"email": "bia@teste.com", "senha": "123"})
        self.app.executar("cancelar_inscricao", {"evento_id": evento})
        self.app.executar("sair", {})
        self.app.executar("login", {"email": "caio@teste.com", "senha": "123"})
        self.assertEqual(self.app.estado()["inscricoes"][0]["status"], "Confirmada")
        self.sistema.banco.fechar()
        self.sistema = SistemaEventFlow(self.caminho)
        self.assertEqual(self.sistema.eventos[0].titulo, "Festival editado")
        self.assertEqual(self.sistema.eventos[0].inscricoes[1].status.value, "Confirmada")
        self.assertEqual(self.sistema.eventos[0].contratacoes[1].equipe.nome, "Equipe B")

    def test_regras_de_sessao_e_dados_privados(self):
        with self.assertRaises(PermissionError):
            self.app.executar("criar_evento", {})
        self.app.executar("demo", {})
        publico = self.app.estado()["publicados"][0]
        self.assertNotIn("inscricoes", publico)
        self.assertNotIn("contratacoes", publico)
        self.app.executar("login", {"email": "bia@eventflow.com", "senha": "123"})
        with self.assertRaises(PermissionError):
            self.app.executar("cancelar_evento", {"evento_id": publico["id"]})

    def test_data_invalida_e_formato_para_edicao(self):
        self.app.executar("cadastro", {"nome": "Ana", "email": "ana@teste.com", "senha": "123", "tipo": "organizador"})
        dados = {"titulo": "Festival", "descricao": "Música", "data_hora": "2026-02-31T18:00", "local": "Praça", "categoria": "Cultura", "vagas": "1"}
        with self.assertRaises(ValueError):
            self.app.executar("criar_evento", dados)
        self.assertEqual([], self.app.estado()["meus_eventos"])
        dados["data_hora"] = "2026-12-20T18:30"
        self.app.executar("criar_evento", dados)
        evento = self.app.estado()["meus_eventos"][0]
        self.assertEqual("20/12/2026 às 18:30", evento["data_hora"])
        self.assertEqual("2026-12-20T18:30", evento["data_hora_input"])

    @unittest.skipUnless(shutil.which("node"), "Node.js indisponível para testar o JavaScript")
    def test_formulario_e_botoes_da_interface_principal(self):
        script = Path(__file__).with_name("test_interface_frontend.js")
        resultado = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True)
        self.assertEqual(0, resultado.returncode, resultado.stderr)

    def _post(self, token="segredo", origem="http://127.0.0.1:12345", caminho="/api/acao"):
        corpo = json.dumps({"acao": "resumo", "dados": {}}).encode()
        req = object.__new__(Requisicoes)
        req.server = SimpleNamespace(server_port=12345, token="segredo", aplicacao=self.app, ultima_presenca=0)
        self.servidor_simulado = req.server
        req.headers = {"Host": "127.0.0.1:12345", "Origin": origem,
                       "X-EventFlow-Token": token, "Content-Length": str(len(corpo))}
        req.path = caminho
        req.rfile = io.BytesIO(corpo)
        req.wfile = io.BytesIO()
        resposta = []
        req.send_response = resposta.append
        req.send_header = lambda *args: None
        req.end_headers = lambda: None
        req.do_POST()
        return resposta[0], json.loads(req.wfile.getvalue())

    def test_protecao_de_requisicao_e_resumo(self):
        self.assertEqual(self._post(token="errado")[0], 403)
        self.assertEqual(self._post(origem="http://outro.site")[0], 403)
        status, resposta = self._post()
        self.assertEqual(status, 200)
        self.assertEqual(resposta["resultado"]["usuarios"], 0)

    def test_presenca_exige_token_valido(self):
        with patch("interface_web.time.monotonic", return_value=123.0):
            self.assertEqual(self._post(token="errado", caminho="/api/presenca")[0], 403)
            self.assertEqual(self.servidor_simulado.ultima_presenca, 0)
            self.assertEqual(self._post(caminho="/api/presenca")[0], 200)
            self.assertEqual(self.servidor_simulado.ultima_presenca, 123.0)

    def test_monitor_encerra_quando_interface_para_de_responder(self):
        servidor = MagicMock(ultima_presenca=0)
        parar = MagicMock()
        parar.wait.side_effect = [False] * 37
        relogio = iter(range(0, 186, 5))
        acompanhar_interface(servidor, parar, relogio=lambda: next(relogio))
        servidor.shutdown.assert_called_once()

    def test_monitor_tolera_suspensao_do_computador(self):
        servidor = MagicMock(ultima_presenca=0)
        parar = MagicMock()
        parar.wait.side_effect = [False, True]
        relogio = iter([0, 600])
        acompanhar_interface(servidor, parar, relogio=lambda: next(relogio))
        servidor.shutdown.assert_not_called()
        self.assertEqual(600, servidor.ultima_presenca)

    def test_servidor_nao_depende_do_processo_inicial_do_navegador(self):
        servidor = MagicMock(server_port=12345)
        processo = MagicMock()
        processo.wait.return_value = 0
        sistema = MagicMock()
        with patch("interface_web.localizar_navegador", return_value="edge"), \
             patch("interface_web.SistemaEventFlow", return_value=sistema), \
             patch("interface_web.ServidorEventFlow", return_value=servidor), \
             patch("interface_web.subprocess.Popen", return_value=processo) as abrir, \
             patch("builtins.print"):
            from interface_web import executar
            executar()
        abrir.assert_called_once_with(["edge", "--app=http://127.0.0.1:12345/"])
        servidor.serve_forever.assert_called_once()
        servidor.shutdown.assert_not_called()
        servidor.server_close.assert_called_once()
        sistema.banco.fechar.assert_called_once()


if __name__ == "__main__":
    unittest.main()

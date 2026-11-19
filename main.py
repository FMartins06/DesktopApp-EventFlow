"""Demonstração executável de todas as funcionalidades do Nível 1."""

from modelos import (
    EquipeDivulgacao,
    GerenciadorUsuarios,
    Organizador,
    Participante,
    RelatorioEventos,
)


def titulo(texto: str) -> None:
    print(f"\n{'=' * 8} {texto} {'=' * 8}")


def executar_demonstracao() -> None:
    titulo("CADASTRO E AUTENTICAÇÃO")
    usuarios = GerenciadorUsuarios()
    ana = usuarios.cadastrar("Ana", "ana@eventflow.com", "123", "organizador")
    bia = usuarios.cadastrar("Bia", "bia@email.com", "123", "participante")
    caio = usuarios.cadastrar("Caio", "caio@email.com", "123", "participante")
    print("Usuários cadastrados:", len(usuarios.usuarios))
    print("Login realizado por:", usuarios.autenticar("ANA@eventflow.com", "123").nome)

    titulo("HERANÇA E POLIMORFISMO")
    for usuario in usuarios.usuarios:
        print(f"{usuario.__class__.__name__} herda de Usuario -> {usuario.descricao_perfil()}")

    assert isinstance(ana, Organizador)
    assert isinstance(bia, Participante)
    assert isinstance(caio, Participante)

    titulo("CRIAÇÃO, EDIÇÃO E PUBLICAÇÃO")
    evento = ana.criar_evento(
        titulo="Festival de Música",
        descricao="Música ao vivo e praça de alimentação.",
        data_hora="20/12/2026 às 18:00",
        local="Praça Central",
        categoria="Música",
        vagas=1,
    )
    evento.editar(
        ana,
        titulo="Festival EventFlow",
        descricao=evento.descricao,
        data_hora=evento.data_hora,
        local=evento.local,
        categoria=evento.categoria,
        vagas=evento.vagas,
    )
    evento.publicar(ana)
    print(f"{evento.titulo}: {evento.status.value}; responsável: {evento.organizador.nome}")

    titulo("INSCRIÇÕES, VAGAS E LISTA DE ESPERA")
    inscricao_bia = evento.demonstrar_interesse(bia)
    inscricao_caio = evento.demonstrar_interesse(caio)
    print("Bia:", inscricao_bia.status.value)
    print("Caio:", inscricao_caio.status.value)
    evento.cancelar_interesse(bia)
    print("Após Bia cancelar, Caio:", inscricao_caio.status.value)

    titulo("CONTRATAÇÃO, SUBSTITUIÇÃO E CANCELAMENTO")
    midia_local = EquipeDivulgacao("Mídia Local", "Divulgação regional", 250.0)
    alcance_digital = EquipeDivulgacao("Alcance Digital", "Redes sociais", 400.0)
    contratacao_local = evento.contratar_equipe(ana, midia_local)
    contratacao_digital = evento.substituir_equipe(
        ana,
        contratacao_local,
        alcance_digital,
    )
    print("Equipe anterior:", contratacao_local.status.value)
    print("Equipe substituta:", contratacao_digital.status.value)
    evento.cancelar_contratacao(ana, contratacao_digital)
    print("Equipe substituta após cancelamento:", contratacao_digital.status.value)

    titulo("DEPENDÊNCIA: RELATÓRIO")
    relatorio = RelatorioEventos()
    print(relatorio.gerar(ana.eventos))

    titulo("CANCELAMENTO DO EVENTO")
    evento.cancelar(ana)
    print("Evento:", evento.status.value)
    print("Inscrição de Caio:", inscricao_caio.status.value)
    print("Demonstração concluída com sucesso.")


if __name__ == "__main__":
    executar_demonstracao()


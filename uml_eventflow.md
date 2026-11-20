# Diagrama de classes — EventFlow Níveis 1 e 2

O diagrama abaixo usa a notação UML: triângulo para herança, losango preto
para composição, losango branco para agregação, linha para associação e linha
tracejada para dependência.

```mermaid
classDiagram
    direction LR

    class Usuario {
        <<abstract>>
        +nome: str
        +email: str
        +senha: str
        +descricao_perfil() str*
    }

    class Organizador {
        -eventos: list~Evento~
        +descricao_perfil() str
        +criar_evento(...) Evento
    }

    class Participante {
        +descricao_perfil() str
    }

    class GerenciadorUsuarios {
        -usuarios: list~Usuario~
        +cadastrar(nome, email, senha, tipo) Usuario
        +autenticar(email, senha) Usuario
    }

    class Evento {
        +titulo: str
        +descricao: str
        +data_hora: str
        +local: str
        +categoria: str
        +vagas: int
        +status: StatusEvento
        +publicar(organizador)
        +editar(organizador, ...)
        +demonstrar_interesse(participante) Inscricao
        +cancelar_interesse(participante) Inscricao
        +contratar_equipe(organizador, equipe) ContratacaoDivulgacao
        +cancelar_contratacao(organizador, contratacao)
        +substituir_equipe(organizador, contratacao, equipe)
        +cancelar(organizador)
    }

    class Inscricao {
        +participante: Participante
        +status: StatusInscricao
    }

    class EquipeDivulgacao {
        +nome: str
        +servicos: str
        +preco: float
    }

    class ContratacaoDivulgacao {
        +equipe: EquipeDivulgacao
        +status: StatusContratacao
    }

    class RelatorioEventos {
        +gerar(eventos) str
    }

    class SistemaEventFlow {
        +usuarios: GerenciadorUsuarios
        -equipes: list~EquipeDivulgacao~
        +eventos: tuple~Evento~
        +eventos_publicados: tuple~Evento~
        +cadastrar_equipe(...) EquipeDivulgacao
        +inscricoes_de(participante) tuple
        +carregar_dados_demo()
    }

    class MenuEventFlow {
        +sistema: SistemaEventFlow
        +executar()
    }

    Usuario <|-- Organizador : herança
    Usuario <|-- Participante : herança
    GerenciadorUsuarios "1" o-- "0..*" Usuario : agregação
    Organizador "1" -- "0..*" Evento : organiza
    Evento "1" *-- "0..*" Inscricao : composição
    Evento "1" *-- "0..*" ContratacaoDivulgacao : composição
    Inscricao "0..*" --> "1" Participante : associação
    ContratacaoDivulgacao "0..*" --> "1" EquipeDivulgacao : associação
    RelatorioEventos ..> Evento : dependência
    SistemaEventFlow *-- GerenciadorUsuarios : mantém em memória
    SistemaEventFlow o-- EquipeDivulgacao : cataloga
    SistemaEventFlow ..> Evento : consulta
    MenuEventFlow *-- SistemaEventFlow : controla
    MenuEventFlow ..> Usuario : apresenta
```

## Onde está cada relação

- **Herança:** `Organizador` e `Participante` especializam `Usuario`.
- **Polimorfismo:** os dois subtipos implementam `descricao_perfil()` de formas
  diferentes; uma coleção de `Usuario` chama o mesmo método sem conhecer o
  subtipo concreto.
- **Composição:** `Inscricao` e `ContratacaoDivulgacao` são criadas e
  controladas exclusivamente por `Evento`; ao cancelar o evento, suas partes
  ativas também são canceladas.
- **Associação:** um `Organizador` organiza eventos, uma `Inscricao` referencia
  um `Participante` e uma contratação referencia uma `EquipeDivulgacao`.
- **Dependência:** `RelatorioEventos` recebe objetos `Evento` apenas para gerar
  a saída e não os mantém como atributos.
- **Agregação (relação adicional):** `GerenciadorUsuarios` reúne usuários, mas
  eles não dependem dele para existir.

## Camada de aplicação do Nível 2

- **`SistemaEventFlow`:** reúne temporariamente usuários, eventos e equipes e
  oferece as consultas necessárias aos menus. Nada é salvo após o encerramento.
- **`MenuEventFlow`:** apresenta as opções, valida as entradas e encaminha cada
  ação ao modelo responsável, sem duplicar as regras de negócio.


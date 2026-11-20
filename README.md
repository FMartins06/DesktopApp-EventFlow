# EventFlow — Desk App III (Nível 3)

Sistema completo de gerenciamento de eventos em Python, operado por menus no
terminal e com persistência permanente em banco de dados **SQLite**. Esta
versão atende ao Nível 3: todas as funcionalidades estão acessíveis e os dados
continuam disponíveis depois que o programa é fechado e aberto novamente.

A interface gráfica será acrescentada somente no Nível 4.

## Funcionalidades

- cadastro e autenticação de organizadores e participantes;
- menus específicos para cada perfil;
- criação, edição, publicação, consulta e cancelamento de eventos;
- demonstração e cancelamento de interesse;
- controle de vagas e promoção automática da lista de espera;
- cadastro, contratação, cancelamento e substituição de equipes de divulgação;
- consulta de inscrições e contratações;
- relatório resumido dos eventos de cada organizador;
- cenário opcional de demonstração;
- resumo das tabelas do banco exibido no próprio menu;
- persistência automática de todas as alterações.

## Banco de dados

O esquema relacional está escrito em SQL no arquivo [`schema.sql`](schema.sql).
Na primeira execução, a aplicação envia esse script ao SQLite e cria
automaticamente o arquivo `eventflow.db`. O SQLite é um banco relacional real e
transacional incluído na biblioteca padrão do Python, portanto não exige
instalação de servidor ou pacote externo.

O Python concentra a modelagem POO, as regras de negócio e a comunicação com o
banco. O SQL concentra tabelas, chaves, relacionamentos e restrições de
integridade. As consultas de inserção, atualização e leitura são parametrizadas
na camada de persistência para receber com segurança os dados da aplicação.

O esquema possui cinco tabelas relacionadas por chaves primárias e
estrangeiras:

| Tabela | Conteúdo principal |
| --- | --- |
| `usuarios` | organizadores, participantes e credenciais protegidas |
| `eventos` | dados, responsável e estado de cada evento |
| `equipes` | catálogo de equipes de divulgação |
| `inscricoes` | participante, evento, ordem e situação da inscrição |
| `contratacoes` | equipe, evento, ordem e situação da contratação |

As operações são salvas em transações, as chaves estrangeiras ficam ativas e
as senhas são armazenadas como hash PBKDF2 com salt individual, nunca como
texto puro. O modelo relacional completo está em
[modelo_banco.md](modelo_banco.md).

## Modelagem orientada a objetos

| Requisito | Implementação |
| --- | --- |
| Herança | `Organizador` e `Participante` herdam de `Usuario` |
| Polimorfismo | cada subtipo sobrescreve `descricao_perfil()` |
| Composição | `Evento` cria e controla `Inscricao` e `ContratacaoDivulgacao` |
| Associação | organizador–evento, inscrição–participante e contratação–equipe |
| Dependência | `RelatorioEventos` usa os eventos somente durante a geração |
| Agregação | `GerenciadorUsuarios` reúne usuários independentes |

O diagrama de classes completo está em
[uml_eventflow.md](uml_eventflow.md).

## Estrutura

```text
.
├── modelos.py           # classes e regras de negócio
├── schema.sql           # tabelas, chaves e restrições em SQL
├── banco_dados.py       # comunicação entre os objetos e o SQLite
├── aplicacao.py         # serviços da aplicação e menus interativos
├── main.py              # ponto de entrada
├── test_modelos.py      # testes das regras de negócio
├── test_aplicacao.py    # testes da aplicação e dos menus
├── test_banco_dados.py  # testes de persistência e reabertura
├── uml_eventflow.md     # diagrama UML de classes
├── modelo_banco.md      # modelo entidade-relacionamento
└── README.md
```

## Como executar

É necessário ter Python 3.10 ou mais recente. O projeto usa somente a
biblioteca padrão.

```powershell
python .\main.py
```

Se o `python` do Windows apontar para a Microsoft Store, use:

```powershell
uv run --python 3.14 --no-project python .\main.py
```

Para executar os 23 testes automatizados:

```powershell
python -m unittest -v
```

ou:

```powershell
uv run --python 3.14 --no-project python -m unittest -v
```

## Demonstração rápida da persistência

1. Execute `main.py`.
2. Escolha **Carregar dados de demonstração**.
3. Escolha **Ver resumo do banco de dados** para conferir os registros.
4. Saia do programa e execute `main.py` novamente.
5. Consulte os eventos ou faça login: os dados anteriores continuam salvos.

As contas criadas pela demonstração são:

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Organizador | `ana@eventflow.com` | `123` |
| Participante | `bia@eventflow.com` | `123` |
| Participante | `caio@eventflow.com` | `123` |

O arquivo gerado `eventflow.db` não é versionado pelo Git. Para começar uma
demonstração do zero, feche o programa e remova esse arquivo local; na próxima
execução, um banco vazio será criado automaticamente.
# EventFlow — Desk App II (Nível 2)

Sistema de gerenciamento de eventos em Python com um menu de terminal
totalmente funcional. Esta versão atende ao **Nível 2**: todos os modelos e
recursos podem ser acessados por menus, e os dados são mantidos em memória
enquanto o programa está aberto.

Ainda não há banco de dados nem interface gráfica. Esses recursos pertencem,
respectivamente, aos níveis 3 e 4.

## O que está implementado

- menu principal com cadastro, login e consulta de eventos publicados;
- menus separados de organizador e participante;
- criação, edição, publicação, consulta e cancelamento de eventos;
- demonstração e cancelamento de interesse em eventos;
- controle de vagas e promoção automática da lista de espera;
- cadastro, contratação, cancelamento e substituição de equipes de divulgação;
- consulta de inscrições e contratações;
- relatório resumido dos eventos de cada organizador;
- validação de entradas, permissões e regras de negócio;
- cenário opcional de demonstração para agilizar os testes manuais.

## Relações de orientação a objetos

| Requisito | Implementação |
| --- | --- |
| Herança | `Organizador` e `Participante` herdam de `Usuario` |
| Polimorfismo | cada subtipo sobrescreve `descricao_perfil()` |
| Composição | `Evento` cria e controla `Inscricao` e `ContratacaoDivulgacao` |
| Associação | organizador–evento, inscrição–participante e contratação–equipe |
| Dependência | `RelatorioEventos` usa os eventos recebidos somente ao gerar o relatório |
| Agregação | `GerenciadorUsuarios` reúne usuários que existem independentemente |

O diagrama de domínio completo está em [uml_eventflow.md](uml_eventflow.md).

## Menus disponíveis

O **menu principal** permite cadastrar usuários, entrar em uma conta, consultar
eventos publicados e carregar dados opcionais de demonstração.

Depois do login, o **organizador** pode administrar seus eventos, inscrições,
equipes, contratações e relatório. O **participante** pode consultar eventos,
demonstrar interesse, acompanhar suas inscrições e cancelar o interesse.

Todas as listas numeradas aceitam `0` para voltar. Operações inválidas exibem
uma mensagem e retornam ao menu, sem encerrar o programa.

## Estrutura

```text
.
├── modelos.py          # classes e regras de negócio
├── aplicacao.py        # estado em memória e menus interativos
├── main.py             # ponto de entrada do programa
├── test_modelos.py     # testes das regras de negócio
├── test_aplicacao.py   # testes da aplicação e do fluxo de menus
├── uml_eventflow.md    # diagrama de classes em Mermaid
└── README.md
```

## Como executar

É necessário ter Python 3.10 ou mais recente. O projeto usa apenas a biblioteca
padrão, portanto não há dependências para instalar.

Para iniciar o menu:

```powershell
python .\main.py
```

Para executar todos os testes:

```powershell
python -m unittest -v
```

Se o comando `python` do Windows apontar para a Microsoft Store, use o Python
já gerenciado pelo `uv`:

```powershell
uv run --python 3.14 --no-project python .\main.py
uv run --python 3.14 --no-project python -m unittest -v
```

Ao fechar o programa, todos os cadastros são descartados. A opção **Carregar
dados de demonstração** cria as contas abaixo, um evento publicado e duas
equipes de divulgação:

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Organizador | `ana@eventflow.com` | `123` |
| Participante | `bia@eventflow.com` | `123` |
| Participante | `caio@eventflow.com` | `123` |

O diagrama Mermaid é renderizado automaticamente ao abrir o arquivo no GitHub.

## Checklist da entrega do Nível 2

- [x] modelagem com todas as relações solicitadas;
- [x] menu principal funcional;
- [x] menus específicos para todos os perfis;
- [x] acesso a todos os modelos e funcionalidades pelo menu;
- [x] dados mantidos em memória, sem banco de dados;
- [x] testes automatizados;
- [x] diagrama UML;
- [x] publicar a versão atualizada no repositório público;
- [x] gravar o vídeo de até 6 minutos;
- [x] adicionar os links públicos do repositório e do vídeo na entrega.


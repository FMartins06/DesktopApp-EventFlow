# EventFlow — Desk App I (Nível 1)

Modelagem orientada a objetos de um sistema de gerenciamento de eventos,
desenvolvida em Python apenas para os requisitos do **Nível 1**.

Esta etapa não implementa menu, banco de dados ou interface gráfica. Esses
itens pertencem aos níveis seguintes e ficaram intencionalmente fora do
escopo.

## O que está implementado

- cadastro e autenticação de organizadores e participantes;
- criação, edição, publicação e cancelamento de eventos;
- demonstração e cancelamento de interesse;
- controle de vagas e promoção automática da lista de espera;
- contratação, cancelamento e substituição de equipes de divulgação;
- relatório resumido dos eventos;
- validações de permissão e das regras de negócio.

## Relações de orientação a objetos

| Requisito | Implementação |
| --- | --- |
| Herança | `Organizador` e `Participante` herdam de `Usuario` |
| Polimorfismo | cada subtipo sobrescreve `descricao_perfil()` |
| Composição | `Evento` cria e controla `Inscricao` e `ContratacaoDivulgacao` |
| Associação | organizador–evento, inscrição–participante e contratação–equipe |
| Dependência | `RelatorioEventos` usa os eventos recebidos somente ao gerar o relatório |
| Agregação | `GerenciadorUsuarios` reúne usuários que existem independentemente |

O diagrama completo está em [uml_eventflow.md](uml_eventflow.md).

## Estrutura

```text
.
├── modelos.py          # classes e regras de negócio
├── main.py             # demonstração linear de todas as funcionalidades
├── test_modelos.py     # testes automatizados
├── uml_eventflow.md    # diagrama de classes em Mermaid
└── README.md
```

## Como executar

É necessário ter Python 3.10 ou mais recente. O projeto usa apenas a biblioteca
padrão, portanto não há dependências para instalar.

Para ver a demonstração completa:

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

O código retorna uma falha visível se alguma regra não se comportar como
esperado. O diagrama Mermaid é renderizado automaticamente ao abrir o arquivo
no GitHub.

## Checklist da entrega do Nível 1

- [x] modelagem com todas as relações solicitadas;
- [x] funcionalidades executáveis sem interface gráfica;
- [x] testes automatizados;
- [x] diagrama UML;
- [x] criar e publicar o repositório no GitHub;
- [x] gravar o vídeo de até 3 minutos;
- [x] adicionar os links públicos do repositório e do vídeo na entrega.


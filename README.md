<p align="center">
  <img src="interface/logo.png" alt="Logo do EventFlow" width="420">
</p>

# EventFlow — Desk App IV (Nível 4)

Sistema desktop de gerenciamento de eventos em Python, com interface em HTML,
CSS e JavaScript e persistência em **SQLite**. As regras de negócio e a modelagem
orientada a objetos são compartilhadas pelas interfaces disponíveis.

## Tecnologias utilizadas

### Interface

- **HTML:** estrutura das telas da interface principal.
- **CSS:** cores, estilos e organização visual das telas.
- **JavaScript:** interação com o usuário e comunicação com a aplicação.
- **Tkinter:** biblioteca Python utilizada na interface gráfica alternativa.

### Aplicação

- **Python:** implementação das regras de negócio e dos conceitos de orientação a objetos.
- **HTTP e JSON:** comunicação local entre a interface principal e o Python.

### Banco de dados

- **SQLite:** armazenamento local dos usuários, eventos, equipes e demais dados.
- **SQL:** definição das tabelas e realização das operações no banco de dados.

### Testes

- **unittest:** execução dos testes automatizados em Python.
- **Node.js:** execução do teste de JavaScript, quando disponível.

## Interface do aplicativo

A interface principal apresenta um painel inicial com indicadores e eventos em
destaque. O menu lateral permite explorar eventos e acessar as opções disponíveis
para cada perfil:

- **Organizador:** gerenciar eventos e equipes e consultar relatórios.
- **Participante:** explorar eventos e acompanhar suas inscrições.

As telas utilizam HTML, CSS e JavaScript, enquanto o Python processa as ações e
acessa o banco de dados por meio de um servidor local. O aplicativo também oferece
uma interface anterior em Tkinter e um menu de terminal, descritos em **Como
executar**.

## Funcionalidades

- Cadastro e autenticação de organizadores e participantes, com menus por perfil.
- Criação, edição, publicação, consulta e cancelamento de eventos.
- Inscrições, cancelamentos, controle de vagas e promoção da lista de espera.
- Cadastro, contratação, cancelamento e substituição de equipes de divulgação.
- Consulta de inscrições e contratações, perfil e relatório de eventos.
- Dados de demonstração, resumo do banco e gravação automática das alterações.

## Como executar

É necessário Python 3.10 ou mais recente e Microsoft Edge, Google Chrome ou
Chromium instalado. Não é necessário instalar pacotes Python adicionais.
O projeto e seus testes foram executados no Windows com as versões **3.10.20**
e **3.14.3** do Python. Outras versões e sistemas não foram verificados nesta
revisão.

No Windows, o navegador precisa estar em um local padrão de instalação ou
disponível no `PATH` para que o aplicativo consiga encontrá-lo.

```powershell
python .\main.py
```

O aplicativo abre em uma janela própria do navegador em modo de aplicativo. O
Python inicia um servidor acessível apenas neste computador (`127.0.0.1`), que
comunica a interface com os modelos e o banco. Mantenha o programa em execução
enquanto usa a janela; depois de fechá-la, o servidor é encerrado em alguns minutos.
Se a janela não abrir automaticamente, acesse o endereço exibido no terminal.
Algumas configurações de segurança podem bloquear conexões locais necessárias
ao funcionamento.

Para usar o menu de terminal ou a interface gráfica anterior em Tkinter:

```powershell
python .\main.py --terminal
python .\main.py --tk
```

A interface anterior exige que o módulo Tkinter esteja disponível na instalação
do Python. No Linux, ele pode exigir um pacote separado.

## Como usar

Na tela inicial, crie uma conta ou entre com uma conta existente. Para organizar,
abra **Meus eventos**, crie um evento e selecione **Gerenciar** para editá-lo,
publicá-lo, consultar inscrições e administrar contratações. Cadastre equipes na
seção **Equipes** antes de contratá-las.

Como participante, abra **Explorar eventos**, selecione um evento publicado e
clique em **Demonstrar interesse**. Em **Minhas inscrições**, acompanhe a situação
ou cancele o interesse. Ao cancelar uma inscrição confirmada, a primeira pessoa
da lista de espera é promovida automaticamente. A lista também é atendida em
ordem quando o organizador aumenta o número de vagas.

Ao criar ou editar um evento, informe uma data e hora válidas. Na interface
principal, selecione esses dados no formulário; no terminal ou no Tkinter, use
o formato `20/12/2026 às 18:00`. Datas passadas são aceitas. Eventos antigos com
formatos que não sejam reconhecidos continuam disponíveis, mas sua data precisa
ser corrigida ao editá-los.

Para experimentar rapidamente em um banco novo, clique em **Carregar demonstração**
na tela inicial. O exemplo inclui um evento publicado, duas equipes e estas contas:

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Organizador | `ana@eventflow.com` | `123` |
| Participante | `bia@eventflow.com` | `123` |
| Participante | `caio@eventflow.com` | `123` |

A demonstração não é carregada novamente se já estiver presente ou se houver
conflito com os e-mails ou nomes de equipes usados no exemplo.

Após fechar e reabrir o aplicativo, as informações continuam disponíveis. O
botão **Resumo do banco** mostra a quantidade de registros em cada tabela.

## Banco de dados

O SQLite cria automaticamente `eventflow.db` na pasta do projeto, usando o
esquema em [schema.sql](schema.sql). O arquivo de dados não é versionado.
As tabelas de usuários, eventos, equipes, inscrições e contratações possuem
relacionamentos por chaves estrangeiras. As operações são transacionais e as
senhas são armazenadas como hash PBKDF2 com salt individual. O modelo relacional
está em [modelo_banco.md](modelo_banco.md).

## Modelagem orientada a objetos

| Conceito | Implementação |
| --- | --- |
| Herança | `Organizador` e `Participante` herdam de `Usuario`. |
| Polimorfismo | Cada subtipo implementa `descricao_perfil()`. |
| Composição | `Evento` cria e controla inscrições e contratações. |
| Associação | Organizador e evento; inscrição e participante; contratação e equipe. |
| Dependência | `RelatorioEventos` utiliza eventos durante a geração do relatório. |
| Agregação | `GerenciadorUsuarios` reúne usuários independentes. |

O diagrama de classes está em [uml_eventflow.md](uml_eventflow.md).

## Estrutura e testes

- `modelos.py`: classes e regras de negócio.
- `banco_dados.py` e `schema.sql`: persistência e esquema SQLite.
- `aplicacao.py`: serviços da aplicação e menu de terminal.
- `interface_web.py`: servidor local e ligação entre interface e aplicação.
- `interface/`: arquivos HTML, CSS e JavaScript.
- `interface_grafica.py`: interface anterior em Tkinter, disponível com `--tk`.
- `main.py`: ponto de entrada.
- `test_*.py` e `test_interface_frontend.js`: testes automatizados.

Execute os testes com:

```powershell
python -m unittest -v
```

Para executar a suíte completa, o módulo Tkinter precisa estar disponível na
instalação do Python. Os testes da interface Tkinter são ignorados se não houver
acesso a uma tela. Os testes da ponte HTML/Python não dependem de rede.
O teste do JavaScript precisa do Node.js e é ignorado quando ele não está
instalado; nesta revisão, foi usada a versão **24.22.1**. O aplicativo em si
não precisa do Node.js.

## O que cada teste verifica

### Usuários, eventos e relatórios — `test_modelos.py`

- `test_cadastra_subtipos_e_autentica_email_sem_diferenciar_maiusculas`: cadastra e autentica usuários.
- `test_impede_email_duplicado_e_login_invalido`: bloqueia cadastro duplicado e senha errada.
- `test_polimorfismo_retorna_descricoes_especificas`: verifica as descrições dos perfis.
- `test_organizador_fica_associado_ao_evento_criado`: confere o responsável pelo evento.
- `test_edita_e_publica_evento`: edita e publica um evento.
- `test_bloqueia_acoes_do_organizador_errado`: impede ações de outro organizador.
- `test_cria_confirmacao_e_lista_de_espera_por_composicao`: verifica confirmação e lista de espera.
- `test_impede_interesse_duplicado_ou_em_evento_nao_publicado`: bloqueia inscrições indevidas.
- `test_cancelar_interesse_promove_primeiro_da_lista`: promove a primeira pessoa após um cancelamento.
- `test_aumento_de_vagas_promove_lista_em_ordem`: preenche novas vagas pela ordem da lista.
- `test_valida_e_normaliza_data_e_hora`: confere datas válidas e inválidas.
- `test_contrata_equipe_por_composicao_e_impede_duplicidade`: contrata uma equipe e evita repetição.
- `test_cancela_contratacao`: cancela uma contratação.
- `test_substitui_equipe`: troca uma equipe contratada.
- `test_cancelar_evento_cancela_partes_compostas_ativas`: cancela inscrições e contratações do evento.
- `test_nao_reduz_vagas_abaixo_dos_confirmados`: impede reduzir vagas abaixo dos inscritos.
- `test_relatorio_depende_dos_eventos_recebidos_sem_armazena_los`: gera um relatório dos eventos recebidos.

### Aplicação e menu — `test_aplicacao.py`

- `test_reune_eventos_publicados_e_inscricoes_do_participante`: consulta eventos e inscrições.
- `test_dados_demo_criam_usuarios_evento_e_equipes_uma_unica_vez`: carrega a demonstração uma vez.
- `test_conflito_impede_carga_parcial_dos_dados_demo`: evita uma demonstração incompleta em caso de conflito.
- `test_impede_equipes_com_nomes_duplicados`: bloqueia nomes repetidos de equipes.
- `test_fluxo_completo_pelo_menu`: percorre as principais ações no terminal.
- `test_opcao_invalida_e_login_incorreto_nao_encerram_menu`: verifica erros no menu e no login.

### Banco de dados — `test_banco_dados.py`

- `test_aumento_de_vagas_salva_promocao_na_reabertura`: confere se a promoção fica salva.
- `test_dados_completos_continuam_apos_fechar_e_reabrir`: verifica os dados após reabrir o banco.
- `test_esquema_ativa_chaves_estrangeiras`: confere os relacionamentos do banco.
- `test_reabre_evento_com_data_antiga_e_exige_correcao_ao_editar`: mantém dados antigos acessíveis e valida a edição.

### Interface Tkinter — `test_interface_grafica.py`

- `test_fluxo_grafico_evento_inscricoes_e_persistencia`: testa eventos e inscrições pela interface.
- `test_contratacao_substituicao_e_validacao`: testa formulários e contratação de equipes.
- `test_evento_cancelado_nao_exibe_acoes_indisponiveis`: confere os botões de um evento cancelado.

### Interface principal — `test_interface_web.py`

- `test_jornada_completa_e_reabertura`: testa o fluxo principal e a persistência.
- `test_regras_de_sessao_e_dados_privados`: verifica permissões e privacidade dos dados.
- `test_protecao_de_requisicao_e_resumo`: confere a proteção das requisições e o resumo.
- `test_data_invalida_e_formato_para_edicao`: valida a data e prepara o campo de edição.
- `test_formulario_e_botoes_da_interface_principal`: verifica o formulário e os botões usando `test_interface_frontend.js`.
- `test_presenca_exige_token_valido`: verifica a proteção da comunicação com a interface.
- `test_monitor_encerra_quando_interface_para_de_responder`: encerra o servidor após fechar a interface.
- `test_monitor_tolera_suspensao_do_computador`: mantém o servidor após uma pausa longa.
- `test_servidor_nao_depende_do_processo_inicial_do_navegador`: verifica a abertura quando o navegador muda de processo.

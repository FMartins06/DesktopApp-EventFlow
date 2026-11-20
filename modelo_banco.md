# Modelo do banco de dados — EventFlow Nível 3

O esquema executável está em [`schema.sql`](schema.sql). O SQLite cria as
tabelas automaticamente na primeira execução. As linhas representam chaves
estrangeiras e as marcações indicam a cardinalidade.

```mermaid
erDiagram
    USUARIOS ||--o{ EVENTOS : organiza
    USUARIOS ||--o{ INSCRICOES : realiza
    EVENTOS ||--o{ INSCRICOES : recebe
    EVENTOS ||--o{ CONTRATACOES : possui
    EQUIPES ||--o{ CONTRATACOES : participa

    USUARIOS {
        INTEGER id PK
        TEXT nome
        TEXT email UK
        TEXT senha_hash
        TEXT senha_salt
        TEXT tipo
    }

    EVENTOS {
        INTEGER id PK
        INTEGER organizador_id FK
        TEXT titulo
        TEXT descricao
        TEXT data_hora
        TEXT local
        TEXT categoria
        INTEGER vagas
        TEXT status
    }

    EQUIPES {
        INTEGER id PK
        TEXT nome UK
        TEXT servicos
        REAL preco
    }

    INSCRICOES {
        INTEGER id PK
        INTEGER evento_id FK
        INTEGER participante_id FK
        TEXT status
        INTEGER ordem
    }

    CONTRATACOES {
        INTEGER id PK
        INTEGER evento_id FK
        INTEGER equipe_id FK
        TEXT status
        INTEGER ordem
    }
```

## Regras de integridade

- e-mails de usuários e nomes de equipes são únicos;
- todo evento referencia um organizador existente;
- toda inscrição referencia um evento e um participante existentes;
- toda contratação referencia um evento e uma equipe existentes;
- vagas e preços não podem ser negativos;
- os estados aceitos são limitados com restrições `CHECK`;
- inscrições e contratações são removidas em cascata caso o evento seja
  excluído diretamente do banco;
- a ordem das inscrições é persistida para manter a prioridade da lista de
  espera.

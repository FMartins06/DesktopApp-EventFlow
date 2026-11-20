-- Esquema relacional do EventFlow — Desk App III
-- Executado automaticamente pelo banco_dados.py na inicialização.

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    senha_hash TEXT NOT NULL,
    senha_salt TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('organizador', 'participante'))
);

CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizador_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    local TEXT NOT NULL,
    categoria TEXT NOT NULL,
    vagas INTEGER NOT NULL CHECK (vagas >= 1),
    status TEXT NOT NULL CHECK (
        status IN ('RASCUNHO', 'PUBLICADO', 'CANCELADO')
    ),
    FOREIGN KEY (organizador_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS equipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL COLLATE NOCASE UNIQUE,
    servicos TEXT NOT NULL,
    preco REAL NOT NULL CHECK (preco >= 0)
);

CREATE TABLE IF NOT EXISTS inscricoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    participante_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('CONFIRMADA', 'LISTA_ESPERA', 'CANCELADA')
    ),
    ordem INTEGER NOT NULL,
    UNIQUE (evento_id, ordem),
    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
    FOREIGN KEY (participante_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS contratacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    equipe_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ATIVA', 'CANCELADA')),
    ordem INTEGER NOT NULL,
    UNIQUE (evento_id, ordem),
    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
    FOREIGN KEY (equipe_id) REFERENCES equipes(id)
);

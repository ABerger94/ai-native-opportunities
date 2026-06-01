CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS healthcheck (
  id integer PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO healthcheck (id) VALUES (1) ON CONFLICT DO NOTHING;

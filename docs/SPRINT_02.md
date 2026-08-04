# Sprint 2 - Migração para SQLite

## Objetivo

Substituir a persistência em JSON por banco de dados.

## Entregas

- SQLite configurado.
- SQLAlchemy implementado.
- Models criados.
- Repository Pattern aplicado.
- Eventos persistidos no banco.

## Arquitetura

Evento

↓

EventoModel

↓

SQLite

## Resultado

A aplicação deixou de depender de arquivos JSON e passou a utilizar persistência real em banco de dados.

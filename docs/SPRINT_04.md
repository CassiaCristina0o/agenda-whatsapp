# Sprint 4 - Implementação da API

## Objetivo

Disponibilizar as funcionalidades da Agenda através de uma API HTTP, preparando o projeto para a integração com o WhatsApp.

## Entregas

* FastAPI configurado.
* Uvicorn configurado.
* Endpoint para cadastrar eventos.
* Endpoint para listar eventos.
* Endpoint para excluir eventos.
* Dados recebidos através de JSON.
* API integrada ao Service e Repository.
* Testes realizados localmente.

## Arquitetura

Cliente HTTP

↓

FastAPI

↓

EventoDTO

↓

AgendaService

↓

EventoRepository

↓

SQLite

## Resultado

A Agenda passou a disponibilizar suas principais operações através de uma API HTTP, mantendo o SQLite como banco de dados e criando a base para a integração com o WhatsApp.


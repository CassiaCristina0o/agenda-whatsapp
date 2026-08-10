# Sprint 3 - Organização da Arquitetura

## Objetivo

Organizar a aplicação para separar as responsabilidades e preparar o projeto para a futura integração com a API do WhatsApp.

## Entregas

* DTO criado para transferência de dados.
* Service criado para as regras de negócio.
* Repository mantido responsável pelo acesso ao banco.
* Validação e formatação de data e hora implementadas.
* CRUD de cadastro, listagem e exclusão funcionando.

## Arquitetura

Entrada

↓

EventoDTO

↓

AgendaService

↓

Evento

↓

EventoRepository

↓

SQLite

## Resultado

A aplicação passou a ter uma estrutura mais organizada e desacoplada, mantendo o funcionamento da versão local e preparando a base para a próxima etapa: integração com uma API.


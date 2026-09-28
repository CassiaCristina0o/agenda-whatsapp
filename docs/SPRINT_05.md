# Sprint 5 - Integração WhatsApp e Lembretes

## Objetivo

Conectar a Agenda ao WhatsApp: cadastrar e consultar compromissos por mensagem, e avisar automaticamente quando um compromisso se aproxima.

## Entregas

* Evolution API em Docker (PostgreSQL + Redis).
* Endpoint `/webhook` recebendo as mensagens.
* Comandos em linguagem natural: `dentista 25/08 14h`, sem formulário.
* Bot sempre ativo na conversa autorizada: toda mensagem vira comando, sem palavra-gatilho nem sessão.
* Várias linhas numa mesma mensagem, cada uma processada de forma independente.
* Recusa de data no passado, comparando data e hora juntas.
* Data e hora guardadas como `datetime`, não como texto.
* Scheduler em `asyncio` disparando lembretes 1 semana, 3 dias e 3 horas antes, e no último minuto.
* Corte seco: passada a hora marcada, o aviso não é mais enviado.
* Limpeza automática dos compromissos vencidos.
* Proteção anti-loop em duas camadas.
* Suíte de testes sem banco real nem rede.

## Arquitetura

WhatsApp

↓

Evolution API

↓

Webhook FastAPI

↓

WhatsAppService

↓

ComandoService

↓

AgendaService

↓

EventoRepository

↓

SQLite

O Scheduler roda em paralelo, lendo o mesmo repositório e enviando os lembretes pelo WhatsAppService.

## Problemas enfrentados

**Loop de mensagens.** O bot roda no mesmo número que o utiliza, então as respostas dele voltam pelo webhook marcadas como mensagens do usuário. A primeira proteção usava esse marcador, mas ele também bloqueava os comandos legítimos. A solução foi reconhecer o eco pelo ID e pelo texto das mensagens enviadas, com um disjuntor por frequência de envio como segunda camada.

**Palavra-gatilho virou fricção.** A primeira versão exigia acordar o bot com uma palavra antes de mandar o compromisso. Como o número é dedicado ao bot, ele já está esperando o evento, então não havia nada a desambiguar. O gatilho e a sessão foram removidos, e a proteção anti-loop caiu de quatro camadas para duas.

**Data e hora como texto.** O formato anterior impedia ordenar cronologicamente e consultar quais eventos vencem. Foi preciso migrar para uma coluna `datetime`, preservando os registros existentes. As propriedades `data` e `hora` continuaram no modelo, formatadas a partir de `quando`, para não quebrar as camadas que já as exibiam.

**Lembrete perdido em falha de envio.** O scheduler marcava o aviso como enviado antes de enviá-lo. Se a Evolution estivesse fora do ar, o lembrete sumia sem ter chegado. A marcação passou a ocorrer só depois da confirmação.

**Aviso "é agora" chegando atrasado.** O aviso da hora tinha uma tolerância de 1 hora: se o bot ficasse fora do ar, ele era enviado ao voltar, mesmo com o compromisso já começado. Avisar "é agora" depois da hora chega como informação errada. A tolerância virou corte seco na hora marcada. Como isso reduziu a janela do aviso para 60 segundos, o intervalo do scheduler caiu de 60s para 30s, senão uma volta pularia a janela inteira.

**Compromisso vencido encalhado na lista.** A limpeza só apagava o evento depois que todos os lembretes dele tinham sido marcados como tratados. Mas o scheduler só varre o passado recente: um compromisso que vencia com o bot desligado saía dessa janela antes de alguém marcar os avisos perdidos, e ficava na lista para sempre. A limpeza passou a considerar encerrado o evento cujos avisos pendentes já perderam a validade, mesmo sem terem sido marcados.

## Resultado

A Agenda passou a funcionar inteiramente por mensagens de WhatsApp, com a API HTTP e a versão de terminal operando sobre as mesmas camadas. Os compromissos geram avisos automáticos e saem da lista sozinhos depois de vencidos.

# Sprint 6 - Agenda no chat privado

## Objetivo

Oferecer uma agenda pessoal no chat privado do WhatsApp, com a lista de cada pessoa separada das demais.

## Entregas

* `bot-dm/`: atende o chat privado.
* Coluna `remetente` em `EventoModel`, com migração automática do banco existente.
* `AgendaService(remetente=...)` filtrando tudo por dono.
* Lista de números liberados em `autorizados.txt`, relida a cada mensagem.
* Lembrete marcando o dono real de cada compromisso.
* Numeração por posição na lista, não pelo id do banco.

## Como o bot atende

| | bot-dm |
|---|---|
| Onde atende | chat privado |
| Quem pode usar | números em `autorizados.txt` |
| Lista | cada um vê só a própria |
| Origem do remetente | o próprio `remoteJid` |
| Lembrete | uma mensagem por pessoa, no privado dela |

## Decisões

**Numerar pela posição na lista.** O `excluir 3` apaga o terceiro item que a pessoa vê, não o id 3 do banco. O id tem buracos de exclusões anteriores e não segue a ordem cronológica. A posição é resolvida na hora, sobre a mesma lista que foi exibida.

**Exclusão múltipla resolvida em bloco.** `excluir 1,2` converte todas as posições em ids antes de apagar qualquer coisa, senão apagar a posição 1 deslocaria a 2 para o lugar dela, e a segunda exclusão pegaria o evento errado.

## Problemas enfrentados

**Tentativa de prompt injection.** Durante os testes, um contato mandou uma mensagem fingindo ser instrução de sistema. Não funcionou: o bot interpreta comandos por padrão de texto, não é um agente de IA. Mesmo assim, o episódio levou a uma revisão: tudo o que o bot aceita de quem conversa com ele se limita às funções da agenda, sem nenhum comando especial para um número privilegiado.

**WhatsApp bloqueando o envio automatizado.** Depois de uma rajada de mensagens de teste, a conexão da instância caiu e os envios seguintes passaram a falhar de forma silenciosa: a Evolution respondia `201`, a mensagem ficava pendente e virava erro (`messageStubParameters: ["463"]`), sem chegar e sem ficar no histórico. Comparando os ids nos logs, mensagens digitadas à mão no aparelho eram entregues e só as enviadas pela API falhavam. Ou seja, o número não estava bloqueado, o WhatsApp estava barrando a automação de um chip novo. Reiniciar a instância não resolveu. O envio voltou sozinho depois de alguns dias sem rajada.

**Lista compartilhada por engano.** Antes da coluna `remetente`, qualquer pessoa via e apagava os compromissos de todas as outras. A migração precisou ser automática, em `criar_banco()`, para não perder os eventos já cadastrados.

**Lembrete repetido no privado.** O scheduler só marcava os lembretes como enviados se todos os envios dessem certo. No privado é um envio por pessoa: se o envio para uma falhava, as outras recebiam o mesmo lembrete de novo a cada volta. A confirmação passou a ser por pessoa, marcando só o que foi entregue.

**Mensagem sem remetente com acesso a tudo.** Remetente vazio significa "sem filtro", o que faz sentido no terminal e na API, mas não no WhatsApp. Uma mensagem que chegava sem remetente via e apagava a agenda de todos. O webhook passou a ignorar mensagens sem remetente.

**Comandos de excluir apagando o item errado.** `remover siso 20/12 9h` era lido como "excluir as posições 20, 12 e 9", e `todos` sozinho apagava a agenda inteira. Agora excluir com data ou hora na mensagem responde com uma explicação, sem apagar nada, e apagar tudo exige `excluir tudo`.

**Datas escritas sem zero.** `15/8` e `1/10` eram recusadas, e em dezembro `05/01` virava janeiro do ano corrente, já passado. A data passou a ser lida por partes, e uma data sem ano que já passou há mais de seis meses vai para o ano seguinte.

**API aberta na rede local.** As rotas `/eventos` listavam e apagavam os compromissos de todas as pessoas, sem autenticação. Passaram a exigir o cabeçalho `X-Api-Key`; sem `AGENDA_API_TOKEN` configurado, ficam fechadas.

## Resultado

O bot passou a atender cada pessoa no próprio chat privado, com lista separada e lembretes enviados só para o dono. Ninguém vê os compromissos do outro.

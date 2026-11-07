# Agenda WhatsApp - bot de chat privado

Agenda de compromissos no chat privado do WhatsApp:

- só responde números listados em `autorizados.txt`;
- cada pessoa vê apenas a própria lista;
- o lembrete chega no privado de cada pessoa.

## Rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # preencha EVOLUTION_API_KEY
cp autorizados.txt.exemplo autorizados.txt # coloque os números liberados
uvicorn app:app --host 0.0.0.0 --port 8000
```

Aponte o webhook da Evolution para `http://SEU_HOST:8000/webhook`.

As rotas `/eventos` exigem o cabeçalho `X-Api-Key` com o valor de
`AGENDA_API_TOKEN`. Sem essa variável, elas ficam fechadas.

## Testes

```bash
python3 testes.py
```

## Arquivos principais

| Arquivo | Papel |
|---|---|
| `services/whatsapp_service.py` | recebe o webhook e envia, filtrando pelo `autorizados.txt` |
| `app.py` | envia um lembrete por pessoa, no privado |
| `autorizados.txt` | números liberados (fica fora do Git; use o `.exemplo`) |

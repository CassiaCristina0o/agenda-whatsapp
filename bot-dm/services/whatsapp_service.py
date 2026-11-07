"""Comunicacao com a Evolution API: leitura do webhook, envio e protecao anti-loop."""

import os
import time
from collections import deque

import requests
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://localhost:8080")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("EVOLUTION_INSTANCE", "agenda-whatsapp")

TIMEOUT = 10

LIMITE_ENVIOS = 8
JANELA_ENVIOS = 60

ARQUIVO_AUTORIZADOS = os.getenv("PRIVADO_AUTORIZADOS_ARQUIVO", "autorizados.txt")

SUFIXO_PV = "@s.whatsapp.net"


def carregar_autorizados() -> set[str]:
    try:
        with open(ARQUIVO_AUTORIZADOS, encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()
    except FileNotFoundError:
        return set()

    numeros = set()

    for linha in linhas:
        limpo = linha.split("#", 1)[0].strip()

        if not limpo:
            continue

        numeros.add("".join(c for c in limpo if c.isdigit()))

    return {n for n in numeros if n}


class WhatsAppService:
    def __init__(self):
        self._ids_enviados: deque[str] = deque(maxlen=100)
        self._textos_enviados: deque[str] = deque(maxlen=20)
        self._envios_recentes: deque[float] = deque()

    def _aceita_jid(self, jid: str | None) -> bool:
        if not jid or not jid.endswith(SUFIXO_PV):
            return False

        return jid.split("@")[0] in carregar_autorizados()

    def _remetente_de(self, key: dict) -> str | None:
        jid = key.get("remoteJid") or ""

        return jid.split("@")[0] or None

    @staticmethod
    def _extrair_texto(message: dict) -> str | None:
        if not message:
            return None

        texto = message.get("conversation")

        if not texto:
            texto = message.get("extendedTextMessage", {}).get("text")

        return texto

    def processar_webhook(self, dados: dict) -> dict | None:
        if dados.get("event") != "messages.upsert":
            return None

        data = dados.get("data", {})
        key = data.get("key", {})

        remote_jid = key.get("remoteJid")

        if not self._aceita_jid(remote_jid):
            print(f"IGNORADO (conversa nao atendida): {remote_jid}")
            return None

        mensagem_id = key.get("id")

        if mensagem_id and mensagem_id in self._ids_enviados:
            print(f"IGNORADO (eco do proprio bot): {mensagem_id}")
            return None

        texto = self._extrair_texto(data.get("message", {}))

        if not texto or not texto.strip():
            return None

        texto = texto.strip()

        if texto in self._textos_enviados:
            print("IGNORADO (eco do proprio bot, por texto)")
            return None

        remetente = self._remetente_de(key)

        if not remetente:
            print("IGNORADO (sem remetente)")
            return None

        resultado = {
            "destino": remote_jid,
            "remetente": remetente,
            "mensagem_id": mensagem_id,
            "texto": texto,
            "comando": texto,
            "from_me": key.get("fromMe", False),
            "data_hora": dados.get("date_time"),
        }

        print("COMANDO RECEBIDO:", resultado)

        return resultado

    def _disjuntor_abriu(self) -> bool:
        agora = time.monotonic()

        while self._envios_recentes and agora - self._envios_recentes[0] > JANELA_ENVIOS:
            self._envios_recentes.popleft()

        if len(self._envios_recentes) >= LIMITE_ENVIOS:
            print(
                f"DISJUNTOR: {LIMITE_ENVIOS} envios em {JANELA_ENVIOS}s. "
                "Bloqueando envios por seguranca."
            )
            return True

        self._envios_recentes.append(agora)

        return False

    def enviar_mensagem(self, numero: str, texto: str) -> dict | None:
        if not self._aceita_jid(numero):
            print(f"ENVIO BLOQUEADO (destino nao autorizado): {numero}")
            return None

        if self._disjuntor_abriu():
            return None

        if not API_KEY:
            print("ENVIO ABORTADO: EVOLUTION_API_KEY nao configurada no .env")
            return None

        url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE}"

        payload = {"number": numero, "text": texto}

        self._textos_enviados.append(payload["text"].strip())

        try:
            response = requests.post(
                url,
                headers={
                    "apikey": API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=TIMEOUT,
            )
        except requests.RequestException as erro:
            print(f"ERRO AO ENVIAR: {erro}")
            return None

        print("RESPOSTA EVOLUTION:", response.status_code)

        if response.status_code >= 400:
            print(response.text)
            return None

        try:
            corpo = response.json()
        except ValueError:
            return None

        enviado_id = (corpo or {}).get("key", {}).get("id")

        if enviado_id:
            self._ids_enviados.append(enviado_id)

        return corpo

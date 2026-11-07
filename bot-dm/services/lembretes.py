"""Regras dos lembretes: quando cada aviso vence e quando perde a validade."""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

CATALOGO = {
    "1s": (timedelta(weeks=1), "Falta 1 semana"),
    "3d": (timedelta(days=3), "Faltam 3 dias"),
    "3h": (timedelta(hours=3), "Faltam 3 horas"),
    "0": (timedelta(minutes=1), "É agora"),
}

ATIVOS = [
    codigo.strip()
    for codigo in os.getenv("LEMBRETES", "1s,3d,3h,0").split(",")
    if codigo.strip() in CATALOGO
]

ATRASO_TOLERADO = timedelta(hours=int(os.getenv("ATRASO_TOLERADO_HORAS", "1")))

JANELA_VISIVEL = timedelta(minutes=int(os.getenv("MINUTOS_VISIVEL_APOS", "2")))


def _limite(quando: datetime) -> datetime:
    return quando


def _codigos(texto: str | None) -> set[str]:
    return {c for c in (texto or "").split(",") if c}


def _texto(codigos: set[str]) -> str:
    return ",".join(sorted(codigos))


def ja_vencidos(quando: datetime, agora: datetime) -> str:
    vencidos = {
        codigo
        for codigo in ATIVOS
        if quando - CATALOGO[codigo][0] <= agora
    }

    return _texto(vencidos)


def devidos(quando: datetime, enviados: str | None, agora: datetime) -> list[str]:
    pendentes = [c for c in ATIVOS if c not in _codigos(enviados)]
    disparar = []

    for codigo in pendentes:
        antecedencia, _ = CATALOGO[codigo]
        momento = quando - antecedencia

        if agora < momento:
            continue

        if agora >= _limite(quando):
            continue

        disparar.append(codigo)

    return disparar


def obsoletos(quando: datetime, enviados: str | None, agora: datetime) -> list[str]:
    perdidos = []

    for codigo in ATIVOS:
        if codigo in _codigos(enviados):
            continue

        if agora >= _limite(quando):
            perdidos.append(codigo)

    return perdidos


def concluido(enviados: str | None) -> bool:
    return set(ATIVOS) <= _codigos(enviados)


def encerrado(quando: datetime, enviados: str | None, agora: datetime) -> bool:
    pendentes = set(ATIVOS) - _codigos(enviados)

    return all(agora >= _limite(quando) for codigo in pendentes)


def frase(titulo: str, quando: datetime, codigo: str) -> str:
    if codigo == "0":
        return f"⏰ *Agora:* {titulo} às {quando:%H:%M}"

    _, anuncio = CATALOGO[codigo]

    return f"🔔 *{anuncio}:* {titulo} — {quando:%d/%m} às {quando:%H:%M}"

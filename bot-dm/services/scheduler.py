"""Laco em segundo plano que envia os lembretes e limpa os vencidos."""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from database.database import SessionLocal
from database.repository import EventoRepository
from services import lembretes

load_dotenv()

INTERVALO = int(os.getenv("INTERVALO_LEMBRETES_SEGUNDOS", "30"))


def pendentes(
    agora: datetime | None = None,
) -> tuple[list[tuple[str | None, str]], list[tuple[int, list[str], str | None]]]:
    agora = agora or datetime.now()
    session = SessionLocal()

    try:
        repository = EventoRepository(session)
        inicio = agora - lembretes.ATRASO_TOLERADO

        frases = []
        confirmar = []

        for evento in repository.listar_a_partir_de(inicio):
            vencidos = lembretes.obsoletos(
                evento.quando, evento.lembretes_enviados, agora
            )

            if vencidos:
                repository.marcar_lembretes(evento.id, vencidos)

            disparar = lembretes.devidos(
                evento.quando, evento.lembretes_enviados, agora
            )

            if not disparar:
                continue

            for codigo in disparar:
                frases.append((
                    evento.remetente,
                    lembretes.frase(evento.titulo, evento.quando, codigo),
                ))

            confirmar.append((evento.id, disparar, evento.remetente))

        return frases, confirmar
    finally:
        session.close()


def limpar_vencidos(agora: datetime | None = None) -> int:
    agora = agora or datetime.now()
    session = SessionLocal()

    try:
        repository = EventoRepository(session)

        ids = [
            evento.id
            for evento in repository.listar_anteriores_a(
                agora - lembretes.JANELA_VISIVEL
            )
            if lembretes.encerrado(
                evento.quando, evento.lembretes_enviados, agora
            )
        ]

        return repository.excluir_por_ids(ids)
    finally:
        session.close()


def confirmar_envio(marcacoes: list[tuple[int, list[str]]]) -> None:
    session = SessionLocal()

    try:
        repository = EventoRepository(session)

        for evento_id, codigos in marcacoes:
            repository.marcar_lembretes(evento_id, codigos)
    finally:
        session.close()


def por_remetente(
    frases: list[tuple[str | None, str]],
) -> list[tuple[str, list[str]]]:
    levas = []

    for remetente in sorted({r for r, _ in frases if r}):
        linhas = [frase for r, frase in frases if r == remetente]
        levas.append(("\n".join(linhas), [remetente]))

    return levas


async def rodar(enviar, intervalo: int = INTERVALO, agrupar=por_remetente) -> None:
    print(f"SCHEDULER ligado: verificando lembretes a cada {intervalo}s")

    while True:
        try:
            frases, marcacoes = await asyncio.to_thread(pendentes)

            if frases:
                levas = agrupar(frases)
                print(
                    f"LEMBRETES a enviar: {len(frases)} em {len(levas)} envio(s)"
                )

                entregues = set()
                falhou = False

                for texto, mencionar in levas:
                    if await asyncio.to_thread(enviar, texto, mencionar):
                        entregues.update(mencionar)
                    else:
                        falhou = True

                confirmar = [
                    (evento_id, codigos)
                    for evento_id, codigos, remetente in marcacoes
                    if not falhou or remetente in entregues
                ]

                if confirmar:
                    await asyncio.to_thread(confirmar_envio, confirmar)

                if falhou:
                    print(
                        "ENVIO FALHOU: lembretes seguem pendentes "
                        "para a proxima volta"
                    )

            removidos = await asyncio.to_thread(limpar_vencidos)

            if removidos:
                print(f"LIMPEZA: {removidos} evento(s) vencido(s) removido(s)")

        except asyncio.CancelledError:
            raise
        except Exception as erro:
            print(f"ERRO NO SCHEDULER: {erro}")

        await asyncio.sleep(intervalo)

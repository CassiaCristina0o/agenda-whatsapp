"""API do bot da agenda no chat privado: recebe o webhook da Evolution e envia os lembretes."""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException

from dto.evento_dto import EventoDTO
from database.database import criar_banco, SessionLocal
from database.repository import EventoRepository
from services.agenda_services import AgendaService
from services.comando_service import ComandoService
from services.whatsapp_service import WhatsAppService, SUFIXO_PV
from services import scheduler

criar_banco()

API_TOKEN = os.getenv("AGENDA_API_TOKEN")

whatsapp_service = WhatsAppService()


def enviar_lembrete(texto: str, mencionar: list[str] | None = None) -> bool:
    if not mencionar:
        return False

    jid = f"{mencionar[0]}{SUFIXO_PV}"

    return bool(whatsapp_service.enviar_mensagem(jid, texto))


def criar_service(remetente: str | None = None):
    session = SessionLocal()
    repository = EventoRepository(session)
    return session, AgendaService(repository, remetente=remetente)


def exigir_token(x_api_key: str | None = Header(default=None)):
    if not API_TOKEN or x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Não autorizado")


def obter_service():
    session, service = criar_service()

    try:
        yield service
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tarefa = asyncio.create_task(
        scheduler.rodar(enviar_lembrete)
    )

    yield

    tarefa.cancel()

    try:
        await tarefa
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Agenda WhatsApp (privado)", lifespan=lifespan)


@app.get("/")
def inicio():
    return {"status": "online"}


@app.post("/eventos", dependencies=[Depends(exigir_token)])
def criar_evento(
    dados: EventoDTO, service: AgendaService = Depends(obter_service)
):
    try:
        service.adicionar(dados)
        return {"mensagem": "Evento cadastrado com sucesso"}
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@app.get("/eventos", dependencies=[Depends(exigir_token)])
def listar_eventos(service: AgendaService = Depends(obter_service)):
    eventos = service.listar()

    return [
        {
            "id": evento.id,
            "titulo": evento.titulo,
            "data": evento.data,
            "hora": evento.hora,
        }
        for evento in eventos
    ]


@app.delete("/eventos/{evento_id}", dependencies=[Depends(exigir_token)])
def excluir_evento(
    evento_id: int, service: AgendaService = Depends(obter_service)
):
    resultado = service.excluir(evento_id)

    if not resultado:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    return {"mensagem": "Evento excluído com sucesso"}


@app.post("/webhook")
def receber_webhook(dados: dict):
    try:
        resultado = whatsapp_service.processar_webhook(dados)

        if not resultado:
            return {"status": "received"}

        destino = resultado["destino"]
        comando = resultado["comando"]
        remetente = resultado["remetente"]

        session, service = criar_service(remetente)

        try:
            resposta = ComandoService(service).executar(comando)
        finally:
            session.close()

    except Exception as erro:
        print(f"ERRO NO WEBHOOK: {erro}")
        return {"status": "received"}

    whatsapp_service.enviar_mensagem(destino, resposta)

    return {"status": "received"}

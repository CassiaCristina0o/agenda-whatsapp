from fastapi import FastAPI

from dto.evento_dto import EventoDTO
from database.database import criar_banco, SessionLocal
from database.repository import EventoRepository
from services.agenda_services import AgendaService


app = FastAPI(title="Agenda WhatsApp")

criar_banco()


@app.get("/")
def inicio():
    return {"status": "online"}


@app.post("/eventos")
def criar_evento(dados: EventoDTO):
    session = SessionLocal()
    repository = EventoRepository(session)
    service = AgendaService(repository)

    service.adicionar(dados)

    session.close()

    return {"mensagem": "Evento cadastrado com sucesso"}

@app.get("/eventos")
def listar_eventos():
    session = SessionLocal()
    repository = EventoRepository(session)
    service = AgendaService(repository)

    eventos = service.listar()

    session.close()

    return eventos 

@app.delete("/eventos/{evento_id}")
def excluir_evento(evento_id: int):
    session = SessionLocal()
    repository = EventoRepository(session)
    service = AgendaService(repository)

    resultado = service.excluir(evento_id)

    session.close()

    if not resultado:
        return {"mensagem": "Evento não encontrado"}
    return {"mensagem": "Evento excluido com sucesso"}
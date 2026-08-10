from sqlalchemy.orm import Session

from evento import Evento
from .models import EventoModel


class EventoRepository:
    """Responsável por acessar a tabela de eventos."""

    def __init__(self, session: Session):
        self.session = session

    def salvar(self, evento: Evento) -> None:
        evento_model = EventoModel(
            titulo=evento.titulo,
            data=evento.data,
            hora=evento.hora,
        )

        self.session.add(evento_model)
        self.session.commit()

    def listar(self) -> list[EventoModel]:
        return self.session.query(EventoModel).all()

    def excluir(self, evento_id: int) -> bool:
        evento = (
            self.session.query(EventoModel)
            .filter_by(id=evento_id)
            .first()
        )

        if evento is None:
            return False

        self.session.delete(evento)
        self.session.commit()

        return True

    def atualizar(
        self,
        evento_id: int,
        titulo: str,
        data: str,
        hora: str
    ) -> bool:

        evento = (
            self.session.query(EventoModel)
            .filter_by(id=evento_id)
            .first()
        )

        if evento is None:
            return False

        evento.titulo = titulo
        evento.data = data
        evento.hora = hora

        self.session.commit()

        return True
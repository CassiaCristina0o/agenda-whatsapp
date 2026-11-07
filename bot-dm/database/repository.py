"""Acesso aos eventos no banco."""

from datetime import datetime

from sqlalchemy.orm import Session

from evento import Evento
from .models import EventoModel


class EventoRepository:
    def __init__(self, session: Session):
        self.session = session

    def salvar(
        self,
        evento: Evento,
        lembretes_enviados: str = "",
        remetente: str | None = None,
    ) -> EventoModel:
        evento_model = EventoModel(
            titulo=evento.titulo,
            quando=evento.quando(),
            lembretes_enviados=lembretes_enviados,
            remetente=remetente,
        )

        self.session.add(evento_model)
        self.session.commit()
        self.session.refresh(evento_model)

        return evento_model

    def listar(
        self,
        remetente: str | None = None,
        desde: datetime | None = None,
    ) -> list[EventoModel]:
        consulta = self.session.query(EventoModel).order_by(EventoModel.quando, EventoModel.id)

        if remetente is not None:
            consulta = consulta.filter_by(remetente=remetente)

        if desde is not None:
            consulta = consulta.filter(EventoModel.quando >= desde)

        return consulta.all()

    def listar_a_partir_de(self, momento: datetime) -> list[EventoModel]:
        return (
            self.session.query(EventoModel)
            .filter(EventoModel.quando >= momento)
            .order_by(EventoModel.quando, EventoModel.id)
            .all()
        )

    def _buscar(self, evento_id: int) -> EventoModel | None:
        return (
            self.session.query(EventoModel)
            .filter_by(id=evento_id)
            .first()
        )

    def marcar_lembretes(self, evento_id: int, codigos: list[str]) -> None:
        evento = self._buscar(evento_id)

        if evento is None:
            return

        atuais = {
            codigo
            for codigo in (evento.lembretes_enviados or "").split(",")
            if codigo
        }

        evento.lembretes_enviados = ",".join(sorted(atuais | set(codigos)))
        self.session.commit()

    def excluir(self, evento_id: int) -> bool:
        evento = self._buscar(evento_id)

        if evento is None:
            return False

        self.session.delete(evento)
        self.session.commit()

        return True

    def listar_anteriores_a(self, limite: datetime) -> list[EventoModel]:
        return (
            self.session.query(EventoModel)
            .filter(EventoModel.quando < limite)
            .all()
        )

    def excluir_por_ids(self, ids: list[int]) -> int:
        if not ids:
            return 0

        quantidade = (
            self.session.query(EventoModel)
            .filter(EventoModel.id.in_(ids))
            .delete(synchronize_session=False)
        )
        self.session.commit()

        return quantidade

    def excluir_todos(self, remetente: str | None = None) -> int:
        consulta = self.session.query(EventoModel)

        if remetente is not None:
            consulta = consulta.filter_by(remetente=remetente)

        quantidade = consulta.delete()
        self.session.commit()

        return quantidade

    def atualizar(
        self,
        evento_id: int,
        titulo: str,
        quando: datetime,
    ) -> bool:
        evento = self._buscar(evento_id)

        if evento is None:
            return False

        evento.titulo = titulo
        evento.quando = quando

        self.session.commit()

        return True

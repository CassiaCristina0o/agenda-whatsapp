from evento import Evento
from database.repository import EventoRepository
from dto.evento_dto import EventoDTO


class AgendaService:

    def __init__(self, repository: EventoRepository):
        self.repository = repository

    def adicionar(self, dto: EventoDTO) -> None:
        evento = Evento(
            dto.titulo,
            dto.data,
            dto.hora
        )

        self.repository.salvar(evento)

    def listar(self):
        return self.repository.listar()

    def excluir(self, evento_id: int) -> bool:
        return self.repository.excluir(evento_id)
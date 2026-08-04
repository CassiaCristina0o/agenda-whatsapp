from evento import Evento
from database.database import SessionLocal
from database.repository import EventoRepository


class Agenda:
    """Gerencia os eventos da agenda."""

    def __init__(self):

        self.session = SessionLocal()
        self.repository = EventoRepository(self.session)

    def adicionar(self, titulo: str, data: str, hora: str) -> None:

        evento = Evento(titulo, data, hora)
        self.repository.salvar(evento)

    def listar(self) -> None:
        eventos = self.repository.listar()

        if not eventos:
            print("\nNenhum evento cadastrado.\n")
            return

        print("\n📅 Eventos\n")

        for indice, evento in enumerate(eventos, start=1):
            print(
                f"{indice}. "
                f"{evento.data} - "
                f"{evento.hora} - "
                f"{evento.titulo}"
                )
            
        print()
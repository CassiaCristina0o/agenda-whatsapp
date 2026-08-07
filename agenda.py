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

        for evento in eventos:
            print(
                f"{evento.id}. "
                f"{evento.titulo} - "
                f"{evento.data} - "
                f"{evento.hora}"
                )
            
        print()

    def excluir(self, evento_id: int) -> None:

        sucesso = self.repository.excluir(evento_id)

        if sucesso:
            print("\n✅ Evento removido com sucesso.\n")
        else:
            print ("\n❌ Evento não encontrado.\n")
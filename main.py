from database.database import criar_banco, SessionLocal
from database.repository import EventoRepository
from dto.evento_dto import EventoDTO
from services.agenda_services import AgendaService


def exibir_menu() -> None:
    print("=== AI Agenda ===")
    print("1 - Novo evento")
    print("2 - Listar eventos")
    print("3 - Excluir evento")
    print("4 - Sair")

def cadastrar_evento(service: AgendaService) -> None:
    titulo = input("Título: ")
    data = input("Data: ")
    hora = input("Hora: ")

    dto = EventoDTO(
        titulo=titulo,
        data=data,
        hora=hora
    )

    try:
        service.adicionar(dto)
        print("\n✅ Evento cadastrado.\n")
    except ValueError as erro:
        print(f"\n❌ {erro}\n")

def listar_eventos(service: AgendaService) -> None:
    eventos = service.listar()

    if not eventos:
        print("\nNenhum evento cadastrado.\n")
        return

    print ("\n📅 Eventos\n")

    for evento in eventos:
        print (
            f"{evento.id}: "
            f"{evento.titulo} - "
            f"{evento.data} - "
            f"{evento.hora}"
        )
    print ()


def excluir_evento(service: AgendaService) -> None:
    try:
        evento_id = int (input("ID do Evento: "))
        service.excluir(evento_id)
        print("\n✅ Evento excluído.\n")

    except ValueError:
        print("\n informe um valor válido.\n")


def main():

    criar_banco()

    session = SessionLocal()
    repository = EventoRepository(session)
    service = AgendaService(repository)


    while True:
        exibir_menu()

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            cadastrar_evento(service)

        elif opcao == "2":
            listar_eventos(service)

        elif opcao == "3":
            excluir_evento(service)

        elif opcao == "4":
            print("\nAté logo!")
            break

        else:
            print("\n❌ Opção inválida.\n")


if __name__ == "__main__":
    main()
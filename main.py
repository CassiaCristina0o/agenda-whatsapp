from agenda import Agenda
from database.database import criar_banco


def exibir_menu() -> None:
    print("=== AI Agenda ===")
    print("1 - Novo evento")
    print("2 - Listar eventos")
    print("3 - Excluir evento")
    print("4 - Sair")

def cadastrar_evento(agenda: Agenda) -> None:
    titulo = input("Título: ")
    data = input("Data: ")
    hora = input("Hora: ")

    try:
        agenda.adicionar(titulo, data, hora)
        print("\n✅ Evento cadastrado.\n")
    except ValueError as erro:
        print(f"\n❌ {erro}\n")

def listar_eventos(agenda: Agenda) -> None:
    agenda.listar()

def excluir_evento(agenda: Agenda) -> None:
    try:
        evento_id = int (input("ID do Evento: "))
        agenda.excluir(evento_id)

    except ValueError:
        print("\n informe um valor válido.\n")


def main():

    criar_banco()

    agenda = Agenda()

    while True:
        exibir_menu()

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            cadastrar_evento(agenda)

        elif opcao == "2":
            listar_eventos(agenda)

        elif opcao == "3":
            excluir_evento(agenda)

        elif opcao == "4":
            print("\nAté logo!")
            break

        else:
            print("\n❌ Opção inválida.\n")


if __name__ == "__main__":
    main()
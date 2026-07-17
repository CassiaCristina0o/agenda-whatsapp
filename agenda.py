import json

from evento import Evento


class Agenda:
    """Gerencia os eventos da agenda."""

    def __init__(self):
        self.eventos: list[Evento] = []
        self.carregar()

    def adicionar(self, titulo: str, data: str, hora: str) -> None:
        evento = Evento(titulo, data, hora)
        self.eventos.append(evento)
        self.salvar()

    def listar(self) -> None:
        if not self.eventos:
            print("\nNenhum evento cadastrado.\n")
            return

        print("\n📅 Eventos\n")

        for indice, evento in enumerate(self.eventos, start=1):
            print(f"{indice}. {evento}")

        print()

    def salvar(self) -> None:
        dados = [evento.to_dict() for evento in self.eventos]

        with open("agenda.json", "w", encoding="utf-8") as arquivo:
            json.dump(
                dados,
                arquivo,
                indent=4,
                ensure_ascii=False
            )

    def carregar(self) -> None:
        try:
            with open("agenda.json", "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            self.eventos = [
                Evento.from_dict(item)
                for item in dados
            ]

        except (FileNotFoundError, json.JSONDecodeError):
            self.eventos = []
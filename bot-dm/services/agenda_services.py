"""Regras da agenda: cadastrar, listar e excluir compromissos."""

from datetime import datetime

from evento import Evento
from database.repository import EventoRepository
from dto.evento_dto import EventoDTO
from services import lembretes


class AgendaService:
    def __init__(self, repository: EventoRepository, remetente: str | None = None):
        self.repository = repository
        self.remetente = remetente

    def adicionar(self, dto: EventoDTO):
        evento = Evento(
            dto.titulo,
            dto.data,
            dto.hora
        )

        agora = datetime.now()

        if evento.quando() < agora:
            raise ValueError("Essa data já passou.")

        salvo = self.repository.salvar(
            evento,
            lembretes.ja_vencidos(evento.quando(), agora),
            remetente=self.remetente,
        )

        return salvo

    def listar(self):
        return self.repository.listar(
            remetente=self.remetente,
            desde=datetime.now() - lembretes.JANELA_VISIVEL,
        )

    def excluir(self, evento_id: int) -> bool:
        return self.repository.excluir(evento_id)

    def excluir_pela_posicao(self, posicao: int) -> bool:
        eventos = self.listar()

        if posicao < 1 or posicao > len(eventos):
            return False

        return self.repository.excluir(eventos[posicao - 1].id)

    def excluir_pelas_posicoes(self, posicoes: list[int]) -> tuple[int, list[int]]:
        eventos = self.listar()

        ids = []
        invalidas = []

        for posicao in posicoes:
            if 1 <= posicao <= len(eventos):
                ids.append(eventos[posicao - 1].id)
            else:
                invalidas.append(posicao)

        removidos = self.repository.excluir_por_ids(ids)

        return removidos, invalidas

    def excluir_todos(self) -> int:
        return self.repository.excluir_todos(remetente=self.remetente)

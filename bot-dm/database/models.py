"""Tabela de eventos."""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EventoModel(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    quando = Column(DateTime, nullable=False, index=True)

    lembretes_enviados = Column(String, nullable=False, default="")

    remetente = Column(String, nullable=True, index=True)

    @property
    def data(self) -> str:
        return self.quando.strftime("%d/%m/%y")

    @property
    def hora(self) -> str:
        return self.quando.strftime("%H:%M")

    def __str__(self) -> str:
        return f"{self.data} - {self.hora} - {self.titulo}"

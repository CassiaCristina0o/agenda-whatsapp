from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Classe base para todos os modelos do banco
Base = declarative_base()


class EventoModel(Base):
    """Tabela de eventos."""

    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    data = Column(String, nullable=False)
    hora = Column(String, nullable=False)
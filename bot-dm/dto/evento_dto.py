"""Dados de entrada para cadastrar um evento."""

from dataclasses import dataclass

@dataclass
class EventoDTO:
    titulo: str
    data: str
    hora: str

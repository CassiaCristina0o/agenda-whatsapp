"""Classe Evento: validacao e formatacao de data e hora."""

import re
from datetime import datetime

class Evento:
    def  __init__(self,titulo: str, data: str, hora: str):
        self.titulo = titulo
        self.data = self.formatar_data(data)
        self.hora = self.formatar_hora(hora)
    
    def __str__(self)-> str:
        return f"{self.data} - {self.hora} - {self.titulo}"

    @staticmethod
    def formatar_data(data: str) -> str:
        partes = [p for p in re.split(r"\D+", data) if p]

        if len(partes) == 1:
            digitos = partes[0]

            if len(digitos) not in (4, 6, 8):
                raise ValueError("Data inválida.")

            partes = [digitos[:2], digitos[2:4], digitos[4:]]

        if len(partes) < 2:
            raise ValueError("Data inválida.")

        dia, mes = partes[0], partes[1]
        ano = partes[2] if len(partes) > 2 and partes[2] else None
        hoje = datetime.now().date()

        try:
            if ano is None:
                data_final = datetime(hoje.year, int(mes), int(dia)).date()

                if (hoje - data_final).days > 182:
                    data_final = datetime(hoje.year + 1, int(mes), int(dia)).date()
            else:
                formato = "%y" if len(ano) == 2 else "%Y"
                data_final = datetime.strptime(
                    f"{dia}/{mes}/{ano}", f"%d/%m/{formato}"
                ).date()
        except ValueError:
            raise ValueError("Data inválida.")

        return data_final.strftime("%d/%m/%y")

    @staticmethod
    def formatar_hora(hora: str) -> str:
        hora = re.sub (r"\D", "", hora)

        if len(hora) == 1:
            hora = f"0{hora}00"
        elif len(hora) == 2:
            hora = f"{hora}00"
        elif len(hora) == 3:
            hora = f"0{hora}"

        try:
            return datetime.strptime(
                hora, "%H%M"
            ).strftime("%H:%M")
        except ValueError:
            raise ValueError("Hora inválida.")

    def quando(self) -> datetime:
        return datetime.strptime(
            f"{self.data} {self.hora}", "%d/%m/%y %H:%M"
        )

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "data": self.data,
            "hora": self.hora
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Evento":
        return cls(
            titulo=dados["titulo"],
            data=dados["data"],
            hora=dados["hora"]
        )

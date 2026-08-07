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
        data = re.sub(r"\D","", data)

        if len (data) == 4:
            ano = datetime.now().strftime("%y")
            data = data + ano
            formato = "%d%m%y"

        elif len(data) == 6:
            formato = "%d%m%y"

        elif len(data) == 8:
            formato = "%d%m%Y"

        else:
            raise ValueError("Data inválida.")

        try:
            return datetime.strptime(data, formato).strftime("%d/%m/%y")
        except ValueError:
            raise ValueError("Data inválida")

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
            raise ValueError ("Hora inválida")

        
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
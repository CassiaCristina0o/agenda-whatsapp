class Evento:
    """"Representa um compromisso da agenda."""

    def  __init__(self,titulo: str, data: str, hora: str):
        self.titulo = titulo
        self.data = data
        self.hora = hora
    
    def __str__(self)-> str:
        return f"{self.data} - {self.hora} - {self.titulo}"
    
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
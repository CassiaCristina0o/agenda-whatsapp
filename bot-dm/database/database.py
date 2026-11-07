"""Conexao com o SQLite e migracoes do banco."""

from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .models import Base

DATABASE_URL = "sqlite:///agenda.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def _migrar_data_hora_para_quando() -> None:
    inspetor = inspect(engine)

    if "eventos" not in inspetor.get_table_names():
        return

    colunas = {coluna["name"] for coluna in inspetor.get_columns("eventos")}

    if "quando" in colunas:
        return

    print("MIGRANDO banco: data/hora (texto) -> quando (datetime)")

    with engine.begin() as conexao:
        antigos = conexao.execute(
            text("SELECT id, titulo, data, hora FROM eventos")
        ).fetchall()

        convertidos = []
        problemas = []

        for linha in antigos:
            try:
                quando = datetime.strptime(
                    f"{linha.data} {linha.hora}", "%d/%m/%y %H:%M"
                )
                convertidos.append((linha.id, linha.titulo, quando))
            except ValueError:
                problemas.append((linha.id, linha.titulo, linha.data, linha.hora))

        conexao.execute(text("ALTER TABLE eventos RENAME TO eventos_antigos"))

        conexao.execute(text("""
            CREATE TABLE eventos (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                titulo VARCHAR NOT NULL,
                quando DATETIME NOT NULL,
                lembretes_enviados VARCHAR NOT NULL DEFAULT ''
            )
        """))
        conexao.execute(text(
            "CREATE INDEX ix_eventos_quando ON eventos (quando)"
        ))

        for evento_id, titulo, quando in convertidos:
            conexao.execute(
                text(
                    "INSERT INTO eventos (id, titulo, quando, lembretes_enviados) "
                    "VALUES (:id, :titulo, :quando, '')"
                ),
                {"id": evento_id, "titulo": titulo, "quando": quando},
            )

        conexao.execute(text("DROP TABLE eventos_antigos"))

    print(f"MIGRACAO OK: {len(convertidos)} evento(s) convertido(s)")

    for evento_id, titulo, data, hora in problemas:
        print(f"  NAO CONVERTIDO id={evento_id} {titulo!r} data={data!r} hora={hora!r}")


def _migrar_adicionar_remetente() -> None:
    inspetor = inspect(engine)

    if "eventos" not in inspetor.get_table_names():
        return

    colunas = {coluna["name"] for coluna in inspetor.get_columns("eventos")}

    if "remetente" in colunas:
        return

    print("MIGRANDO banco: adicionando coluna remetente")

    with engine.begin() as conexao:
        conexao.execute(text("ALTER TABLE eventos ADD COLUMN remetente VARCHAR"))


def criar_banco():
    _migrar_data_hora_para_quando()
    _migrar_adicionar_remetente()
    Base.metadata.create_all(bind=engine)

"""Interpreta as mensagens do WhatsApp e executa o comando na agenda."""

import re

from services.agenda_services import AgendaService
from dto.evento_dto import EventoDTO

PADRAO_DATA = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")

PADRAO_HORA = re.compile(
    r"\b\d{1,2}\s*(?::|h(?:s|rs|oras)?)\s*\d{0,2}\b",
    re.IGNORECASE,
)

PADRAO_LIGACAO = re.compile(
    r"(?:\s+(?:as|às|à|a|o|no|na|em|de|do|da|dia|para|pra))+$",
    re.IGNORECASE,
)

PADRAO_COMEMORACAO = re.compile(r"^a+h+$", re.IGNORECASE)

VERBOS_NOVO = {"n", "novo", "nova", "add", "adicionar", "criar", "marcar", "agendar"}
VERBOS_LISTAR = {"l", "/l", "listar", "lista", "ver", "eventos", "agenda"}
VERBOS_EXCLUIR = {"e", "/e", "x", "excluir", "apagar", "remover", "deletar", "cancelar"}
VERBOS_AJUDA = {"ajuda", "help", "?"}
VERBOS_REGRAS = {
    "r", "/r", "regras", "regra", "opcoes", "opções", "opcao", "opção",
    "menu", "comandos",
}

TUDO_PALAVRAS = {"tudo", "todos", "todas"}

SAUDACOES_BASE = {
    "oi", "ola", "olá", "opa", "eae", "e ai", "e aí",
    "bom dia", "boa tarde", "boa noite",
}

SAUDACAO = "🤖 Agenda ativa. Pode mandar.\n_`regras` para ver o que eu faço._"

BOAS_VINDAS_INTRO = (
    "👋 Olá! Seja bem-vindo(a) à Agenda.\n\n"
    "Aqui você organiza seus compromissos e eu te lembro "
    "1 semana, 3 dias e 3 horas antes, e de novo na hora.\n\n"
)


def _eh_saudacao(texto: str) -> bool:
    normalizado = texto.lower().strip(" .!")

    return normalizado in SAUDACOES_BASE or any(
        normalizado == f"{base} agenda" for base in SAUDACOES_BASE
    )


ATALHOS_MENU = {"1": "listar", "2": "excluir", "3": "regras"}

PADRAO_ATALHO_EXCLUIR = re.compile(r"^2[.\s]+(\d+)$")


def montar_regras() -> str:
    return (
        "Funções\n\n"
        "* cadastro: evento data e hora\n"
        "* mostrar eventos: 1 - listar - /l\n"
        "* apagar evento: 2 - excluir - /e (ex: excluir 3 ou excluir 1,2)\n"
        "* apagar tudo: excluir tudo\n"
        "* funções: 3 - regras - /r"
    )


def interpretar(comando: str) -> dict:
    texto = (comando or "").strip()

    if not texto:
        return {"acao": "saudacao"}

    if _eh_saudacao(texto):
        return {"acao": "boas_vindas"}

    if PADRAO_COMEMORACAO.match(texto):
        return {"acao": "comemoracao"}

    atalho_excluir = PADRAO_ATALHO_EXCLUIR.match(texto)

    if atalho_excluir:
        return {"acao": "excluir", "posicao": int(atalho_excluir.group(1))}

    if texto in ATALHOS_MENU:
        texto = ATALHOS_MENU[texto]

    partes = texto.split(maxsplit=1)
    verbo = partes[0].lower().rstrip(":")
    resto = partes[1].strip() if len(partes) > 1 else ""

    if verbo in VERBOS_AJUDA or verbo in VERBOS_REGRAS:
        return {"acao": "regras"}

    if verbo in VERBOS_LISTAR:
        return {"acao": "listar"}

    if verbo in VERBOS_EXCLUIR:
        if resto.lower() in TUDO_PALAVRAS:
            return {"acao": "excluir_tudo"}

        if PADRAO_DATA.search(resto) or PADRAO_HORA.search(resto):
            return {
                "acao": "erro",
                "mensagem": (
                    "Para apagar, use o número da lista: `excluir 3` ou `excluir 1,2`.\n"
                    "Para cadastrar, comece pelo nome: `academia 15/12 7h`."
                ),
            }

        encontrados = re.findall(r"\d+", resto)

        if not encontrados:
            return {
                "acao": "erro",
                "mensagem": (
                    "Preciso do número do evento.\n"
                    "Exemplo: `excluir 3` ou `excluir 1,2`\n"
                    "Use `listar` para ver os números."
                ),
            }

        posicoes = [int(n) for n in encontrados]

        if len(posicoes) == 1:
            return {"acao": "excluir", "posicao": posicoes[0]}

        return {"acao": "excluir_varios", "posicoes": posicoes}

    if verbo in VERBOS_NOVO:
        descricao = resto
    else:
        descricao = texto

    return _interpretar_novo(descricao)


def _interpretar_novo(descricao: str) -> dict:
    if not descricao:
        return {
            "acao": "erro",
            "mensagem": (
                "Faltou o evento.\n"
                "Exemplo: `dentista 25/08 14h`"
            ),
        }

    encontrou_data = PADRAO_DATA.search(descricao)

    if not encontrou_data:
        return {
            "acao": "erro",
            "mensagem": (
                "Não encontrei a data.\n"
                "Exemplo: `dentista 25/08 14h`"
            ),
        }

    data = encontrou_data.group()
    sobra = descricao.replace(data, " ", 1)

    encontrou_hora = PADRAO_HORA.search(sobra)

    if not encontrou_hora:
        return {
            "acao": "erro",
            "mensagem": (
                "Não encontrei o horário.\n"
                "Exemplo: `dentista 25/08 14h`"
            ),
        }

    hora = encontrou_hora.group()
    titulo = sobra.replace(hora, " ", 1)
    titulo = re.sub(r"\s+", " ", titulo).strip(" -,;.")
    titulo = PADRAO_LIGACAO.sub("", titulo).strip()

    if not titulo:
        return {
            "acao": "erro",
            "mensagem": (
                "Faltou o nome do evento.\n"
                "Exemplo: `dentista 25/08 14h`"
            ),
        }

    return {
        "acao": "novo",
        "titulo": titulo,
        "data": data,
        "hora": hora,
    }


class ComandoService:
    def __init__(self, agenda: AgendaService):
        self.agenda = agenda

    def executar(self, comando: str) -> str:
        linhas = [
            linha.strip()
            for linha in (comando or "").splitlines()
            if linha.strip()
        ]

        if len(linhas) > 1:
            return self._executar_lote(linhas)

        return self._executar_linha(comando or "")

    def _executar_lote(self, linhas: list[str]) -> str:
        resultados = []

        for linha in linhas:
            acao = interpretar(linha)

            if acao["acao"] == "novo":
                resultados.append(self._novo_compacto(acao, linha))
            elif acao["acao"] == "erro":
                motivo = acao["mensagem"].splitlines()[0].rstrip(".")
                resultados.append(f"❌ {linha} — {motivo.lower()}")
            else:
                resultados.append(self._executar_linha(linha))

        return "\n".join(resultados)

    def _cadastrar(self, acao: dict):
        dto = EventoDTO(
            titulo=acao["titulo"],
            data=acao["data"],
            hora=acao["hora"],
        )

        return self.agenda.adicionar(dto)

    def _novo_compacto(self, acao: dict, linha: str) -> str:
        try:
            evento = self._cadastrar(acao)
        except ValueError as erro:
            return f"❌ {linha} — {erro}"

        return f"✅ {evento.titulo} — {evento.data} às {evento.hora}"

    def _executar_linha(self, comando: str) -> str:
        acao = interpretar(comando)
        nome = acao["acao"]

        if nome == "saudacao":
            return SAUDACAO

        if nome == "boas_vindas":
            return BOAS_VINDAS_INTRO + montar_regras()

        if nome == "comemoracao":
            return "lelek"

        if nome == "regras":
            return montar_regras()

        if nome == "erro":
            return acao["mensagem"]

        if nome == "listar":
            return self._listar()

        if nome == "novo":
            return self._novo(acao)

        if nome == "excluir":
            return self._excluir(acao["posicao"])

        if nome == "excluir_varios":
            return self._excluir_varios(acao["posicoes"])

        if nome == "excluir_tudo":
            return self._excluir_tudo()

        return SAUDACAO

    def _listar(self) -> str:
        eventos = self.agenda.listar()

        if not eventos:
            return "Nenhum evento cadastrado."

        linhas = [
            f"{posicao}. {evento.titulo} — {evento.data} às {evento.hora}"
            for posicao, evento in enumerate(eventos, start=1)
        ]

        return "📅 *Eventos*\n\n" + "\n".join(linhas)

    def _novo(self, acao: dict) -> str:
        try:
            evento = self._cadastrar(acao)
        except ValueError as erro:
            return f"❌ {erro}"

        posicao = self._posicao_atual(evento)

        return (
            "✅ Evento cadastrado\n\n"
            f"{posicao}. {evento.titulo} — {evento.data} às {evento.hora}"
        )

    def _posicao_atual(self, evento) -> int:
        for posicao, item in enumerate(self.agenda.listar(), start=1):
            if item.id == evento.id:
                return posicao

        return 0

    def _excluir(self, posicao: int) -> str:
        if self.agenda.excluir_pela_posicao(posicao):
            return f"🗑️ Evento {posicao} excluído."

        return f"❌ Não encontrei o evento {posicao}."

    def _excluir_varios(self, posicoes: list[int]) -> str:
        removidos, invalidas = self.agenda.excluir_pelas_posicoes(posicoes)
        partes = []

        if removidos:
            partes.append(f"🗑️ {removidos} evento(s) excluído(s).")

        if invalidas:
            lista = ", ".join(str(p) for p in invalidas)
            partes.append(f"❌ Não encontrei: {lista}.")

        return "\n".join(partes)

    def _excluir_tudo(self) -> str:
        quantidade = self.agenda.excluir_todos()

        if not quantidade:
            return "Nenhum evento para excluir."

        return f"🗑️ Seus eventos apagados: {quantidade} excluído(s)."

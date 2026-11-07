"""Testes da agenda, sem banco real nem rede. Rode com: python testes.py"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import sqlalchemy
from sqlalchemy.orm import sessionmaker

import evento
from evento import Evento
from database.models import Base, EventoModel
from database.repository import EventoRepository
from services import lembretes, scheduler
from services.agenda_services import AgendaService
from services.comando_service import ComandoService, interpretar
from services.whatsapp_service import WhatsAppService

falhas = []


def checa(nome: str, obtido, esperado) -> None:
    ok = obtido == esperado
    print(f"  [{'PASS' if ok else 'FALHOU'}] {nome}")

    if not ok:
        falhas.append(f"{nome}: esperava {esperado!r}, veio {obtido!r}")


def banco():
    caminho = Path(tempfile.mkdtemp()) / "teste.db"
    engine = sqlalchemy.create_engine(f"sqlite:///{caminho}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def agenda_limpa(remetente=None):
    Sessao = banco()
    return Sessao, ComandoService(AgendaService(EventoRepository(Sessao()), remetente=remetente))


def teste_parser():
    print("\nPARSER")
    checa("vazio vira saudacao", interpretar("")["acao"], "saudacao")
    checa("listar", interpretar("listar")["acao"], "listar")
    checa("abreviacao l", interpretar("l")["acao"], "listar")
    checa("abreviacao E maiuscula", interpretar("E 3")["posicao"], 3)
    checa("apagar o 12", interpretar("apagar o 12")["posicao"], 12)
    checa("excluir varios com virgula",
          interpretar("excluir 1,2")["posicoes"], [1, 2])
    checa("excluir varios vira acao excluir_varios",
          interpretar("excluir 1,2")["acao"], "excluir_varios")
    checa("excluir varios com espaco depois da virgula",
          interpretar("e 1, 2, 3")["posicoes"], [1, 2, 3])
    checa("regras", interpretar("r")["acao"], "regras")
    checa("alias /r tambem funciona", interpretar("/r")["acao"], "regras")
    checa("alias /l tambem funciona", interpretar("/l")["acao"], "listar")
    checa("alias /L maiusculo tambem funciona", interpretar("/L")["acao"], "listar")
    checa("alias /e tambem funciona", interpretar("/e 3")["posicao"], 3)

    checa("atalho 1 equivale a listar", interpretar("1")["acao"], "listar")
    checa("atalho 3 equivale a regras", interpretar("3")["acao"], "regras")
    checa("atalho 2 pede o numero do evento",
          interpretar("2")["acao"], "erro")
    checa("numero fora do menu nao vira atalho",
          interpretar("9")["acao"], "erro")

    checa("atalho 2 com numero junto exclui direto",
          interpretar("2 3")["posicao"], 3)
    checa("atalho 2 com ponto e numero tambem exclui",
          interpretar("2. 3")["posicao"], 3)
    checa("atalho 2 com numero grudado tambem exclui",
          interpretar("2.5")["posicao"], 5)

    for palavra in ("tudo", "todos", "Todas"):
        checa(f"'{palavra}' sozinho nao apaga a agenda",
              interpretar(palavra)["acao"], "erro")
    checa("excluir tudo tambem apaga a agenda inteira",
          interpretar("excluir tudo")["acao"], "excluir_tudo")
    checa("e todos tambem funciona",
          interpretar("e todos")["acao"], "excluir_tudo")

    checa("ah sozinho vira comemoracao", interpretar("ah")["acao"], "comemoracao")
    checa("ahh tambem vira comemoracao", interpretar("ahh")["acao"], "comemoracao")
    checa("aah tambem vira comemoracao", interpretar("AaH")["acao"], "comemoracao")
    checa("frase comecando com ah nao vira comemoracao",
          interpretar("ah preciso marcar dentista 25/08 14h")["acao"], "novo")

    checa("saudacao simples", interpretar("oi")["acao"], "boas_vindas")
    checa("saudacao com acento", interpretar("Olá!")["acao"], "boas_vindas")
    checa("saudacao composta", interpretar("bom dia")["acao"], "boas_vindas")
    checa("saudacao seguida de agenda", interpretar("bom dia agenda")["acao"], "boas_vindas")
    checa("saudacao nao atrapalha evento real",
          interpretar("boa tarde com o dentista 25/08 14h")["acao"], "novo")

    novo = interpretar("novo aula de ingles 26/08 19h")
    checa("titulo com espacos", novo["titulo"], "aula de ingles")
    checa("data", novo["data"], "26/08")
    checa("hora", novo["hora"], "19h")

    checa("sem verbo tambem cadastra", interpretar("dentista 25/08 14h")["acao"], "novo")
    checa("ligacoes removidas", interpretar("reuniao no dia 30/08 as 9h")["titulo"], "reuniao")
    checa("titulo comecando com E", interpretar("exame 25/08 9h")["titulo"], "exame")
    checa("titulo comecando com S", interpretar("show 01/09 22h")["titulo"], "show")
    checa("sem data da erro", interpretar("almoco")["acao"], "erro")


def teste_data_passada():
    print("\nDATA PASSADA")
    _, cs = agenda_limpa()
    agora = datetime.now()

    passado = agora - timedelta(hours=2)
    futuro = agora + timedelta(hours=2)

    r = cs.executar(f"passado {passado:%d/%m} {passado:%Hh}")
    checa("hoje mais cedo e recusado", r.startswith("❌"), True)

    r = cs.executar(f"futuro {futuro:%d/%m} {futuro:%Hh}")
    checa("hoje mais tarde e aceito", r.startswith("✅"), True)

    r = cs.executar("festa 01/01/25 20h")
    checa("ano passado e recusado", r.startswith("❌"), True)


def teste_formatos_de_data():
    print("\nFORMATOS DE DATA E VIRADA DE ANO")
    for escrita, esperado in (("15/8", "15/08/"), ("1/10", "01/10/"), ("5/9", "05/09/"),
                              ("25-08", "25/08/"), ("2508", "25/08/")):
        checa(f"'{escrita}' e aceito", Evento.formatar_data(escrita).startswith(esperado), True)

    checa("ano com 4 digitos", Evento.formatar_data("25/08/2031"), "25/08/31")
    checa("ano colado com 8 digitos", Evento.formatar_data("25082031"), "25/08/31")

    for invalida in ("31/02", "13/13", "123", "25"):
        try:
            Evento.formatar_data(invalida)
            resultado = "aceitou"
        except ValueError as erro:
            resultado = str(erro)
        checa(f"'{invalida}' e recusado", resultado, "Data inválida.")

    class DezembroFalso(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 12, 20, 10, 0)

    original = evento.datetime
    evento.datetime = DezembroFalso
    try:
        checa("em dezembro, 05/01 vai para janeiro do ano seguinte",
              Evento.formatar_data("05/01"), "05/01/27")
        checa("em dezembro, 25/12 continua no mesmo ano",
              Evento.formatar_data("25/12"), "25/12/26")
        checa("dia de hoje nao pula para o ano seguinte",
              Evento.formatar_data("20/12"), "20/12/26")
        checa("ontem nao pula para o ano seguinte (vira data passada)",
              Evento.formatar_data("19/12"), "19/12/26")
    finally:
        evento.datetime = original


def teste_lote():
    print("\nVARIAS LINHAS NUMA MENSAGEM")
    _, cs = agenda_limpa()
    depois = datetime.now() + timedelta(days=20)

    resposta = cs.executar(
        f"Dentista {depois:%d/%m} 15h\n"
        "Reuniao 16/08/25 17h\n"
        f"Mercado {depois:%d/%m} 10h"
    )
    linhas = resposta.splitlines()

    checa("uma resposta por linha", len(linhas), 3)
    checa("primeira aceita", linhas[0].startswith("✅"), True)
    checa("data passada recusada no meio", linhas[1].startswith("❌"), True)
    checa("terceira aceita mesmo assim", linhas[2].startswith("✅"), True)
    checa("so as validas entraram", cs.executar("listar").count("\n"), 3)


def teste_excluir_tudo():
    print("\nEXCLUIR TUDO")
    _, cs = agenda_limpa()
    depois = datetime.now() + timedelta(days=5)

    cs.executar(f"Dentista {depois:%d/%m} 15h\nMercado {depois:%d/%m} 10h")

    resposta = cs.executar("excluir tudo")
    checa("confirma a exclusao em massa", "2" in resposta, True)
    checa("agenda fica vazia", cs.executar("listar"), "Nenhum evento cadastrado.")

    resposta_vazia = cs.executar("excluir tudo")
    checa("excluir tudo com agenda ja vazia nao quebra",
          resposta_vazia, "Nenhum evento para excluir.")


def teste_excluir_por_posicao():
    print("\nEXCLUIR PELA POSICAO NA LISTA (nao pelo id do banco)")
    _, cs = agenda_limpa()
    dia = (datetime.now() + timedelta(days=5)).strftime("%d/%m")

    cs.executar(f"Cinema {dia} 20h")
    cs.executar(f"Dentista {dia} 08h")

    listagem = cs.executar("listar").splitlines()
    checa("posicao 1 e o mais cedo (Dentista), nao o id 1 (Cinema)",
          listagem[2].startswith("1. Dentista"), True)
    checa("posicao 2 e o Cinema", listagem[3].startswith("2. Cinema"), True)

    resposta = cs.executar("excluir 1")
    checa("excluiu quem aparece em 1o na lista",
          resposta, "🗑️ Evento 1 excluído.")

    restante = cs.executar("listar")
    checa("sobrou so o Cinema, renumerado como 1",
          restante.splitlines()[2].startswith("1. Cinema"), True)


def teste_vencido_fora_da_lista():
    print("\nCOMPROMISSO VENCIDO NAO APARECE NA AGENDA")
    Sessao, cs = agenda_limpa()

    s = Sessao()
    s.add(EventoModel(
        titulo="Ja passou",
        quando=datetime.now() - timedelta(hours=3),
        lembretes_enviados="1s,3d,3h,0",
    ))
    s.commit()
    s.close()

    listagem = cs.executar("listar")
    checa("vencido nao aparece na listagem", "Ja passou" in listagem, False)
    checa("agenda so com vencido responde como vazia",
          listagem, "Nenhum evento cadastrado.")

    s = Sessao()
    s.add(EventoModel(
        titulo="Comecou agora",
        quando=datetime.now() - timedelta(minutes=1),
    ))
    s.commit()
    s.close()

    checa("o que comecou ha 1 min ainda aparece",
          "Comecou agora" in cs.executar("listar"), True)


def teste_excluir_ignora_vencido():
    print("\nEXCLUIR NAO CONTA O QUE JA VENCEU")
    Sessao, cs = agenda_limpa()
    dia = (datetime.now() + timedelta(days=5)).strftime("%d/%m")

    s = Sessao()
    s.add(EventoModel(
        titulo="Fantasma",
        quando=datetime.now() - timedelta(days=2),
        lembretes_enviados="1s,3d,3h,0",
    ))
    s.commit()
    s.close()

    cs.executar(f"Dentista {dia} 08h")

    listagem = cs.executar("listar").splitlines()
    checa("o unico visivel e o 1 da lista",
          listagem[2].startswith("1. Dentista"), True)

    cs.executar("excluir 1")
    checa("excluir 1 apagou o Dentista, nao o vencido",
          cs.executar("listar"), "Nenhum evento cadastrado.")

    s = Sessao()
    sobrou = {e.titulo for e in s.query(EventoModel).all()}
    s.close()
    checa("vencido segue no banco, so invisivel - quem apaga e o scheduler",
          sobrou, {"Fantasma"})


def teste_excluir_varios():
    print("\nEXCLUIR VARIOS DE UMA VEZ (excluir 1,2)")
    _, cs = agenda_limpa()
    dia = (datetime.now() + timedelta(days=5)).strftime("%d/%m")

    cs.executar(f"Um {dia} 08h")
    cs.executar(f"Dois {dia} 09h")
    cs.executar(f"Tres {dia} 10h")

    resposta = cs.executar("excluir 1,2")
    checa("confirma quantos foram excluidos", resposta, "🗑️ 2 evento(s) excluído(s).")

    restante = cs.executar("listar").splitlines()
    checa("so sobrou o terceiro, renumerado como 1",
          restante[2].startswith("1. Tres"), True)
    checa("nao sobrou mais nada alem dele", len(restante), 3)

    resposta_invalida = cs.executar("excluir 1,9")
    checa("mistura valido e invalido no mesmo pedido",
          resposta_invalida, "🗑️ 1 evento(s) excluído(s).\n❌ Não encontrei: 9.")
    checa("agenda fica vazia depois", cs.executar("listar"), "Nenhum evento cadastrado.")

    for i in range(1, 21):
        cs.executar(f"Item{i} {dia} {i % 24}h")
    for frase in ("remover siso 20/12 9h", "cancelar academia 15/12 7h"):
        checa(f"'{frase}' nao apaga nada", interpretar(frase)["acao"], "erro")
        cs.executar(frase)
    checa("lista continua com os 20 itens",
          cs.executar("listar").count("\n"), 21)


def teste_isolamento_por_remetente():
    print("\nISOLAMENTO POR REMETENTE (cada um ve so a propria lista)")
    Sessao = banco()
    dia = (datetime.now() + timedelta(days=5)).strftime("%d/%m")

    cs_ana = ComandoService(AgendaService(EventoRepository(Sessao()), remetente="ana"))
    cs_bia = ComandoService(AgendaService(EventoRepository(Sessao()), remetente="bia"))

    cs_ana.executar(f"Consulta {dia} 09h")
    cs_bia.executar(f"Reuniao {dia} 15h")
    cs_bia.executar(f"Extra {dia} 20h")

    checa("ana ve so o proprio evento",
          "Consulta" in cs_ana.executar("listar"), True)
    checa("ana nao ve o evento da bia",
          "Reuniao" in cs_ana.executar("listar"), False)
    checa("bia ve os proprios 2 eventos",
          cs_bia.executar("listar").count("\n"), 3)

    resposta = cs_ana.executar("excluir 1")
    checa("ana exclui o proprio evento", resposta, "🗑️ Evento 1 excluído.")
    checa("bia nao foi afetada", cs_bia.executar("listar").count("\n"), 3)

    resposta_tudo = cs_bia.executar("excluir tudo")
    checa("bia apaga so os proprios eventos",
          resposta_tudo, "🗑️ Seus eventos apagados: 2 excluído(s).")
    checa("ana continua sem nada (ja tinha excluido)",
          cs_ana.executar("listar"), "Nenhum evento cadastrado.")


def teste_lembretes():
    print("\nREGRA DE LEMBRETES")
    evento = datetime(2026, 9, 15, 15, 0)
    cadastro = evento - timedelta(days=30)

    enviados = lembretes.ja_vencidos(evento, cadastro)
    checa("cadastro com folga nao pre-marca nada", enviados, "")
    checa("nada dispara no cadastro", lembretes.devidos(evento, enviados, cadastro), [])
    checa("1 semana antes", lembretes.devidos(evento, "", evento - timedelta(weeks=1)), ["1s"])
    checa("nao repete", lembretes.devidos(evento, "1s", evento - timedelta(days=5)), [])
    checa("3 dias antes", lembretes.devidos(evento, "1s", evento - timedelta(days=3)), ["3d"])
    checa("3 horas antes", lembretes.devidos(evento, "1s,3d", evento - timedelta(hours=3)), ["3h"])
    checa("no ultimo minuto antes",
          lembretes.devidos(evento, "1s,3d,3h", evento - timedelta(seconds=30)),
          ["0"])
    checa("na hora marcada ja nao avisa - corte seco",
          lembretes.devidos(evento, "1s,3d,3h", evento), [])

    curto = lembretes.ja_vencidos(evento, evento - timedelta(days=2))
    checa("cadastro em cima da hora ja nasce marcado", curto, "1s,3d")

    checa("fora do ar: aviso previo vencido nao vai",
          lembretes.devidos(evento, "", evento + timedelta(days=2)), [])
    checa("fora do ar 30min: nao avisa atrasado",
          lembretes.devidos(evento, "1s,3d,3h", evento + timedelta(minutes=30)), [])
    checa("fora do ar 5h: nao avisa mais",
          lembretes.devidos(evento, "1s,3d,3h", evento + timedelta(hours=5)), [])

    checa("concluido com tudo enviado", lembretes.concluido("1s,3d,3h,0"), True)
    checa("nao concluido enquanto falta algum", lembretes.concluido("1s,3d,3h"), False)
    checa("nao concluido sem nada enviado", lembretes.concluido(""), False)

    checa("encerrado quando tudo ja foi enviado",
          lembretes.encerrado(evento, "1s,3d,3h,0", evento), True)
    checa("nao encerrado enquanto o '0' ainda pode sair",
          lembretes.encerrado(evento, "1s,3d,3h", evento - timedelta(seconds=30)),
          False)
    checa("encerrado na hora marcada - o '0' perdeu a validade",
          lembretes.encerrado(evento, "1s,3d,3h", evento), True)
    checa("nao encerrado antes do evento acontecer",
          lembretes.encerrado(evento, "", evento - timedelta(days=1)), False)
    checa("encerrado: venceu fora do ar e os pendentes perderam a validade",
          lembretes.encerrado(evento, "1s,3d", evento + timedelta(days=5)), True)


def teste_scheduler():
    print("\nSCHEDULER")
    Sessao = banco()
    scheduler.SessionLocal = Sessao

    limpar_original = scheduler.limpar_vencidos
    scheduler.limpar_vencidos = lambda *a, **k: 0

    agora = datetime.now() + timedelta(seconds=30)
    s = Sessao()
    s.add(EventoModel(
        titulo="Dentista", quando=agora, lembretes_enviados="1s,3d,3h",
        remetente="5511999999999",
    ))
    s.add(EventoModel(titulo="Mercado", quando=agora, lembretes_enviados="1s,3d,3h"))
    s.commit()
    s.close()

    tentativas = []

    def envio(texto, mencionar):
        tentativas.append((texto, mencionar))
        return None if len(tentativas) <= 2 else {"key": {"id": "OK"}}

    async def girar():
        tarefa = asyncio.create_task(scheduler.rodar(envio, intervalo=0.2))
        await asyncio.sleep(1.4)
        tarefa.cancel()
        try:
            await tarefa
        except asyncio.CancelledError:
            pass

    asyncio.run(girar())

    primeiro_texto, primeiro_mencionar = tentativas[0]
    checa("insiste enquanto o envio falha", len(tentativas) >= 3, True)
    checa("envia o evento que tem dono", "Dentista" in primeiro_texto, True)
    checa("evento sem dono nao e enviado", "Mercado" in primeiro_texto, False)
    checa("marca so o dono do compromisso", primeiro_mencionar, ["5511999999999"])

    s = Sessao()
    marcados = [e.lembretes_enviados for e in s.query(EventoModel).all()]
    checa("marcado so depois de chegar", all("0" in m.split(",") for m in marcados), True)
    checa("parou de tentar apos confirmar", len(tentativas), 3)

    scheduler.limpar_vencidos = limpar_original


def teste_limpeza_vencidos():
    print("\nLIMPEZA DE EVENTOS VENCIDOS")
    Sessao = banco()
    scheduler.SessionLocal = Sessao

    ja_concluido = datetime.now() - timedelta(minutes=5)
    recem_comecou = datetime.now() - timedelta(minutes=1)
    no_futuro = datetime.now() + timedelta(hours=2)

    s = Sessao()
    s.add(EventoModel(
        titulo="Terminado ha 5 minutos", quando=ja_concluido,
        lembretes_enviados="1s,3d,3h,0",
    ))
    s.add(EventoModel(
        titulo="Comecou ha 1 minuto", quando=recem_comecou,
        lembretes_enviados="1s,3d,3h",
    ))
    s.add(EventoModel(titulo="Ainda vai acontecer", quando=no_futuro))
    s.add(EventoModel(
        titulo="Venceu com o bot desligado",
        quando=datetime.now() - timedelta(days=5),
        lembretes_enviados="1s,3d",
    ))
    s.commit()
    s.close()

    removidos = scheduler.limpar_vencidos()
    checa("remove quem terminou e ja saiu da lista", removidos, 2)

    s = Sessao()
    restantes = {e.titulo for e in s.query(EventoModel).all()}
    s.close()
    checa("o que comecou agora fica ate sair da lista",
          "Comecou ha 1 minuto" in restantes, True)
    checa("evento futuro nunca e candidato",
          "Ainda vai acontecer" in restantes, True)
    checa("evento vencido com lembrete perdido nao fica encalhado",
          "Venceu com o bot desligado" in restantes, False)


def teste_anti_loop():
    print("\nANTI-LOOP")
    import services.whatsapp_service as pv

    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as arq:
        arq.write("5511911111111\n")
        caminho = arq.name

    original = pv.ARQUIVO_AUTORIZADOS
    pv.ARQUIVO_AUTORIZADOS = caminho

    try:
        w = WhatsAppService()
        liberado = "5511911111111@s.whatsapp.net"

        def pacote(texto, mid="M"):
            return {"event": "messages.upsert", "data": {
                "key": {"remoteJid": liberado, "fromMe": False, "id": mid},
                "message": {"conversation": texto}}}

        checa("bot sempre ativo: qualquer mensagem de numero liberado vale",
              w.processar_webhook(pacote("dentista 25/08 14h"))["comando"],
              "dentista 25/08 14h")
        checa("outra mensagem tambem vale",
              w.processar_webhook(pacote("listar"))["comando"], "listar")

        w._textos_enviados.append("📅 *Eventos*\n\n1. Dentista")
        checa("eco por texto e ignorado",
              w.processar_webhook(pacote("📅 *Eventos*\n\n1. Dentista")), None)

        w._ids_enviados.append("BOT9")
        checa("eco por id e ignorado",
              w.processar_webhook(pacote("qualquer", mid="BOT9")), None)
    finally:
        pv.ARQUIVO_AUTORIZADOS = original
        Path(caminho).unlink(missing_ok=True)


def teste_privado():
    print("\nBOT NO PRIVADO (chat pessoal do numero-bot)")
    import services.whatsapp_service as pv

    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as arq:
        arq.write("# liberados\n5511911111111\n+55 11 92222-2222\n\n")
        caminho = arq.name

    original = pv.ARQUIVO_AUTORIZADOS
    pv.ARQUIVO_AUTORIZADOS = caminho

    try:
        checa("le o txt: ignora comentario e limpa a pontuacao",
              pv.carregar_autorizados(), {"5511911111111", "5511922222222"})

        w = pv.WhatsAppService()

        def pacote(texto, jid):
            return {"event": "messages.upsert", "data": {
                "key": {"remoteJid": jid, "fromMe": False, "id": "M"},
                "message": {"conversation": texto}}}

        liberado = w.processar_webhook(
            pacote("listar", "5511911111111@s.whatsapp.net")
        )
        checa("numero da lista passa", liberado["comando"], "listar")
        checa("remetente vem do proprio remoteJid",
              liberado["remetente"], "5511911111111")
        checa("resposta volta pro PV de quem mandou",
              liberado["destino"], "5511911111111@s.whatsapp.net")

        checa("numero fora da lista e ignorado",
              w.processar_webhook(
                  pacote("listar", "5511000000000@s.whatsapp.net")), None)

        arquivo_ausente = pv.ARQUIVO_AUTORIZADOS
        pv.ARQUIVO_AUTORIZADOS = "/nao/existe/lista.txt"
        try:
            checa("sem arquivo, ninguem fala com o bot",
                  pv.carregar_autorizados(), set())
        finally:
            pv.ARQUIVO_AUTORIZADOS = arquivo_ausente
    finally:
        pv.ARQUIVO_AUTORIZADOS = original
        Path(caminho).unlink(missing_ok=True)


def teste_lembrete_por_remetente():
    print("\nLEMBRETE NO PRIVADO VAI UM A UM")
    frases = [
        ("5511911111111", "⏰ *Agora:* Dentista (hoje 14:00)"),
        ("5511922222222", "⏰ *Agora:* Reuniao (hoje 15:00)"),
        ("5511911111111", "📅 *Em 3 dias:* Viagem"),
        (None, "⏰ *Agora:* Evento sem dono"),
    ]

    levas = scheduler.por_remetente(frases)
    checa("uma leva por dono; sem dono nao vira PV", len(levas), 2)

    por_numero = {mencionar[0]: texto for texto, mencionar in levas}
    checa("cada leva marca so o proprio dono",
          set(por_numero), {"5511911111111", "5511922222222"})
    checa("dono com dois lembretes recebe os dois juntos",
          por_numero["5511911111111"].count("\n"), 1)
    checa("nao vaza o compromisso de um dono pro outro",
          "Reuniao" in por_numero["5511911111111"], False)


def teste_falha_parcial_no_privado():
    print("\nFALHA DE ENVIO PARA UMA PESSOA NAO REPETE PARA AS OUTRAS")
    Sessao = banco()
    scheduler.SessionLocal = Sessao

    limpar_original = scheduler.limpar_vencidos
    scheduler.limpar_vencidos = lambda *a, **k: 0

    quando = datetime.now() + timedelta(hours=2)
    s = Sessao()
    s.add(EventoModel(
        titulo="Dentista", quando=quando, lembretes_enviados="1s,3d",
        remetente="5511911111111",
    ))
    s.add(EventoModel(
        titulo="Reuniao", quando=quando, lembretes_enviados="1s,3d",
        remetente="5511922222222",
    ))
    s.commit()
    s.close()

    recebidos = []

    def envio(texto, mencionar):
        if mencionar == ["5511922222222"]:
            return None
        recebidos.append(mencionar[0])
        return {"key": {"id": "OK"}}

    async def girar():
        tarefa = asyncio.create_task(
            scheduler.rodar(envio, intervalo=0.2, agrupar=scheduler.por_remetente)
        )
        await asyncio.sleep(1)
        tarefa.cancel()
        try:
            await tarefa
        except asyncio.CancelledError:
            pass

    asyncio.run(girar())

    checa("quem recebeu nao recebe de novo", recebidos, ["5511911111111"])

    s = Sessao()
    marcados = {e.titulo: e.lembretes_enviados for e in s.query(EventoModel).all()}
    checa("lembrete entregue fica marcado", "3h" in marcados["Dentista"].split(","), True)
    checa("lembrete que falhou segue pendente", "3h" in marcados["Reuniao"].split(","), False)

    scheduler.limpar_vencidos = limpar_original


if __name__ == "__main__":
    for teste in (
        teste_parser,
        teste_data_passada,
        teste_formatos_de_data,
        teste_lote,
        teste_excluir_tudo,
        teste_excluir_por_posicao,
        teste_vencido_fora_da_lista,
        teste_excluir_ignora_vencido,
        teste_excluir_varios,
        teste_isolamento_por_remetente,
        teste_lembretes,
        teste_scheduler,
        teste_limpeza_vencidos,
        teste_anti_loop,
        teste_privado,
        teste_lembrete_por_remetente,
        teste_falha_parcial_no_privado,
    ):
        teste()

    print("\n" + "=" * 50)

    if falhas:
        print(f"{len(falhas)} FALHA(S):")
        for f in falhas:
            print("  -", f)
    else:
        print("TODOS OS TESTES PASSARAM")

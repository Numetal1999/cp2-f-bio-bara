import random
from datetime import datetime, timedelta

from config import get_mongo_db

TOTAL_EVENTOS = 200
JANELA_HORAS = 24
TTL_SEGUNDOS = 604800


def popular_eventos(colecao):
    colecao.drop()
    colecao.create_index("timestamp", expireAfterSeconds=TTL_SEGUNDOS)

    agora = datetime.now()
    eventos = []
    for _ in range(TOTAL_EVENTOS):
        deslocamento = timedelta(
            hours=random.uniform(0, JANELA_HORAS),
            minutes=random.uniform(0, 60),
        )
        eventos.append({
            "timestamp": agora - deslocamento,
            "tipo": random.choice(["FALHA_LOGIN", "TIMEOUT", "ACESSO_NEGADO"]),
            "ip_origem": f"10.0.{random.randint(0, 5)}.{random.randint(1, 254)}",
        })
    colecao.insert_many(eventos)


def distribuicao_por_hora(colecao):
    pipeline = [
        {"$group": {"_id": {"$hour": "$timestamp"}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return list(colecao.aggregate(pipeline))


def eventos_na_janela(colecao, horas):
    limite = datetime.now() - timedelta(hours=horas)
    return colecao.count_documents({"timestamp": {"$gte": limite}})


def main():
    db = get_mongo_db()
    colecao = db.eventos

    popular_eventos(colecao)
    distribuicao = distribuicao_por_hora(colecao)

    print(f"=== Falhas por hora (ultimas {JANELA_HORAS}h) ===")
    pico_hora, pico_total = None, -1
    for linha in distribuicao:
        hora, total = linha["_id"], linha["total"]
        barra = "#" * total
        print(f"{hora:02d}h | {barra} {total}")
        if total > pico_total:
            pico_hora, pico_total = hora, total

    print(f"Hora de pico: {pico_hora:02d}h ({pico_total} falhas)")

    total_janela = eventos_na_janela(colecao, 6)
    print(f"Eventos nas ultimas 6h: {total_janela}")

    print("Indice TTL ativo: eventos com mais de 7 dias serao removidos automaticamente.")

    # O TTL e decisao de seguranca: log guardado alem do necessario so aumenta o que vaza num incidente.


if __name__ == "__main__":
    main()

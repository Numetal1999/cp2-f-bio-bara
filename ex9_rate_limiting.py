from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from sklearn.ensemble import IsolationForest

from config import get_mongo_db

app = Flask(__name__)

ips_bloqueados = set()


@app.before_request
def registrar_inicio_requisicao():
    if request.path == "/api/analise-acessos":
        return
    request._registro_acesso = {
        "ip": request.remote_addr,
        "rota": request.path,
        "metodo": request.method,
        "timestamp": datetime.now(),
    }

    if request.remote_addr in ips_bloqueados:
        resposta = jsonify({"erro": "muitas requisicoes"})
        resposta.status_code = 429
        resposta.headers["Retry-After"] = "60"
        return resposta


@app.after_request
def completar_registro(response):
    registro = getattr(request, "_registro_acesso", None)
    if registro is not None:
        registro["status"] = response.status_code
        db = get_mongo_db()
        db.acessos.insert_one(registro)
    return response


def analisar_e_bloquear(janela_minutos=1):
    db = get_mongo_db()
    limite = datetime.now() - timedelta(minutes=janela_minutos)

    pipeline = [
        {"$match": {"timestamp": {"$gte": limite}}},
        {"$group": {
            "_id": "$ip",
            "total_requisicoes": {"$sum": 1},
            "total_4xx": {"$sum": {"$cond": [{"$and": [
                {"$gte": ["$status", 400]}, {"$lt": ["$status", 500]}
            ]}, 1, 0]}},
            "rotas_distintas": {"$addToSet": "$rota"},
        }},
        {"$project": {
            "req_por_minuto": {"$divide": ["$total_requisicoes", janela_minutos]},
            "taxa_4xx": {"$divide": ["$total_4xx", "$total_requisicoes"]},
            "rotas_distintas": {"$size": "$rotas_distintas"},
        }},
    ]

    resultados = list(db.acessos.aggregate(pipeline))
    if not resultados:
        return []

    X = [[r["req_por_minuto"], r["taxa_4xx"], r["rotas_distintas"]] for r in resultados]

    detector = IsolationForest(contamination=0.2, random_state=42)
    rotulos = detector.fit_predict(X)

    print("=== Analise de acessos ===")
    for r, rotulo in zip(resultados, rotulos):
        classificacao = "ANOMALIA -> bloqueado" if rotulo == -1 else "normal"
        print(
            f"{r['_id']:15s} [{r['req_por_minuto']:6.1f} req/min | "
            f"4xx {r['taxa_4xx']:.2f} | {r['rotas_distintas']} rotas]  -> {classificacao}"
        )
        if rotulo == -1:
            ips_bloqueados.add(r["_id"])

    return resultados


@app.route("/api/analise-acessos", methods=["POST"])
def rota_analise():
    analisar_e_bloquear()
    return jsonify({"bloqueados": list(ips_bloqueados)}), 200


@app.route("/api/ping")
def ping():
    return jsonify({"pong": True}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5004)

# Bloquear por anomalia (e nao por regra fixa) pode marcar como hostil um usuario legitimo com uso incomum.
# Falso positivo derruba quem deveria acessar, entao o bloqueio precisa de revisao e de prazo (Retry-After).

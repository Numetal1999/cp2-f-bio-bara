import math
from datetime import datetime

import numpy as np
from flask import Flask, request, jsonify
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

from config import get_mongo_db

app = Flask(__name__)

NUM_FEATURES = 4
FEATURE_NOMES = ["falhas_login", "portas_distintas", "bytes_saida", "hora_do_dia"]

modelo = None
metricas_teste = None


def gerar_dataset(n=400, seed=42):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for _ in range(n):
        alto_risco = rng.random() < 0.35
        if alto_risco:
            falhas_login = rng.integers(6, 20)
            portas_distintas = rng.integers(4, 15)
            bytes_saida = rng.integers(30000, 200000)
            hora = rng.integers(0, 6)
            rotulo = 1
        else:
            falhas_login = rng.integers(0, 3)
            portas_distintas = rng.integers(0, 3)
            bytes_saida = rng.integers(200, 15000)
            hora = rng.integers(6, 22)
            rotulo = 0
        X.append([falhas_login, portas_distintas, bytes_saida, hora])
        y.append(rotulo)
    return np.array(X), np.array(y)


def treinar_modelo():
    global modelo, metricas_teste

    X, y = gerar_dataset()
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_treino, y_treino)

    y_pred = modelo.predict(X_teste)
    metricas_teste = {
        "precisao": round(float(precision_score(y_teste, y_pred)), 2),
        "recall": round(float(recall_score(y_teste, y_pred)), 2),
        "f1": round(float(f1_score(y_teste, y_pred)), 2),
        "matriz": confusion_matrix(y_teste, y_pred).tolist(),
    }


def validar_features(corpo):
    if not isinstance(corpo, dict) or "features" not in corpo:
        return None, "corpo deve conter 'features'"

    features = corpo["features"]
    if not isinstance(features, list) or len(features) != NUM_FEATURES:
        return None, f"esperadas {NUM_FEATURES} features, recebidas {len(features) if isinstance(features, list) else 0}"

    valores = []
    for v in features:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None, "features devem ser numericas"
        if not math.isfinite(v):
            return None, "features devem ser numeros finitos"
        valores.append(float(v))

    return valores, None


@app.route("/api/triagem", methods=["POST"])
def triagem():
    corpo = request.get_json(silent=True)
    valores, erro = validar_features(corpo)
    if erro:
        return jsonify({"erro": erro}), 400

    entrada = np.array([valores])
    predicao = modelo.predict(entrada)[0]
    confianca = float(max(modelo.predict_proba(entrada)[0]))

    risco = "alto" if predicao == 1 else "baixo"

    db = get_mongo_db()
    db.previsoes.insert_one({
        "entrada": dict(zip(FEATURE_NOMES, valores)),
        "saida": risco,
        "confianca": round(confianca, 2),
        "timestamp": datetime.now(),
    })

    return jsonify({"risco": risco, "confianca": round(confianca, 2)}), 200


@app.route("/api/modelo/metricas", methods=["GET"])
def metricas():
    resposta = dict(metricas_teste)
    resposta["aviso"] = (
        "acuracia omitida de proposito: com classes desbalanceadas ela "
        "esconde um modelo que erra justamente os casos de alto risco"
    )
    return jsonify(resposta), 200


if __name__ == "__main__":
    treinar_modelo()
    app.run(debug=False, host="0.0.0.0", port=5003)

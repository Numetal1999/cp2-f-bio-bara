from flask import Flask, request, jsonify

from config import get_mysql_connection

app = Flask(__name__)

NIVEL_PARA_APAGAR_QUALQUER = 5

analistas = [
    (1, "ana", "key-ana-001", 5),
    (2, "bruno", "key-bruno-002", 2),
]

incidentes = [
    (1, 1, "Brute force SSH", "critica", "aberto"),
    (2, 2, "Phishing no RH", "media", "aberto"),
]


def preparar_mysql():
    conn = get_mysql_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS incidentes")
    cur.execute("DROP TABLE IF EXISTS analistas")
    cur.execute(
        """
        CREATE TABLE analistas (
            id INT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            api_key VARCHAR(100) UNIQUE NOT NULL,
            nivel INT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE incidentes (
            id INT PRIMARY KEY,
            dono_id INT NOT NULL,
            titulo VARCHAR(200) NOT NULL,
            severidade VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            FOREIGN KEY (dono_id) REFERENCES analistas(id)
        )
        """
    )
    cur.executemany("INSERT INTO analistas (id, nome, api_key, nivel) VALUES (%s, %s, %s, %s)", analistas)
    cur.executemany(
        "INSERT INTO incidentes (id, dono_id, titulo, severidade, status) VALUES (%s, %s, %s, %s, %s)",
        incidentes,
    )
    conn.commit()
    cur.close()
    conn.close()


def autenticar():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, nivel FROM analistas WHERE api_key = %s", (api_key,))
    analista = cur.fetchone()
    cur.close()
    conn.close()
    return analista


@app.route("/api/incidentes/<int:incidente_id>", methods=["GET"])
def obter_incidente(incidente_id):
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM incidentes WHERE id = %s", (incidente_id,))
    incidente = cur.fetchone()
    cur.close()
    conn.close()

    if incidente is None:
        return jsonify({"erro": "incidente nao encontrado"}), 404

    if incidente["dono_id"] != analista["id"] and analista["nivel"] < NIVEL_PARA_APAGAR_QUALQUER:
        return jsonify({"erro": "acesso negado"}), 403

    return jsonify(incidente), 200


@app.route("/api/incidentes", methods=["GET"])
def listar_incidentes():
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    if analista["nivel"] >= NIVEL_PARA_APAGAR_QUALQUER:
        cur.execute("SELECT * FROM incidentes")
    else:
        cur.execute("SELECT * FROM incidentes WHERE dono_id = %s", (analista["id"],))
    linhas = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(linhas), 200


@app.route("/api/incidentes/<int:incidente_id>", methods=["DELETE"])
def apagar_incidente(incidente_id):
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    if analista["nivel"] < NIVEL_PARA_APAGAR_QUALQUER:
        return jsonify({"erro": "acesso negado"}), 403

    conn = get_mysql_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM incidentes WHERE id = %s", (incidente_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify({"erro": "incidente nao encontrado"}), 404

    cur.execute("DELETE FROM incidentes WHERE id = %s", (incidente_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"removido": incidente_id}), 200


if __name__ == "__main__":
    preparar_mysql()
    app.run(debug=False, host="0.0.0.0", port=5001)

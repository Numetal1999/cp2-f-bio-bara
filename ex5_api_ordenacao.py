from flask import Flask, request, jsonify

from config import get_mysql_connection

app = Flask(__name__)

COLUNAS = {"data": "criado_em", "sev": "severidade", "ip": "ip_origem"}
ORDEM = {"asc": "ASC", "desc": "DESC"}
TAMANHO_MAXIMO = 100


def preparar_mysql():
    conn = get_mysql_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS eventos")
    cur.execute(
        """
        CREATE TABLE eventos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            severidade VARCHAR(20) NOT NULL,
            ip_origem VARCHAR(45) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    severidades = ["baixa", "media", "alta", "critica"]
    for i in range(20):
        cur.execute(
            "INSERT INTO eventos (severidade, ip_origem) VALUES (%s, %s)",
            (severidades[i % 4], f"10.0.0.{i}"),
        )
    conn.commit()
    cur.close()
    conn.close()


@app.route("/api/eventos")
def listar_eventos():
    ordenar_por = request.args.get("ordenar_por", "data")
    ordem = request.args.get("ordem", "asc")
    tamanho_raw = request.args.get("tamanho", "20")

    if ordenar_por not in COLUNAS:
        return jsonify({"erro": "campo de ordenacao invalido"}), 400
    if ordem not in ORDEM:
        return jsonify({"erro": "ordem invalida"}), 400

    try:
        tamanho = int(tamanho_raw)
    except ValueError:
        return jsonify({"erro": "tamanho deve ser inteiro"}), 400

    tamanho = max(1, min(tamanho, TAMANHO_MAXIMO))

    coluna_sql = COLUNAS[ordenar_por]
    ordem_sql = ORDEM[ordem]

    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    # LIMIT %s funciona porque LIMIT recebe um valor (dado), que o driver escapa como literal.
    # ORDER BY recebe um identificador (nome de coluna), que o driver nao consegue parametrizar.
    # Identificador nao vem do usuario: vem de mapa fechado (whitelist); dado vai por placeholder.
    query = f"SELECT * FROM eventos ORDER BY {coluna_sql} {ordem_sql} LIMIT %s"
    cur.execute(query, (tamanho,))
    linhas = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(linhas), 200


if __name__ == "__main__":
    preparar_mysql()
    app.run(debug=False, host="0.0.0.0", port=5000)

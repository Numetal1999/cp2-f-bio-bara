import logging
import os

from flask import Flask, request, jsonify
from markupsafe import escape
import mysql.connector

app = Flask(__name__)

DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_NAME = os.environ.get("MYSQL_DATABASE", "seguranca")

NIVEL_PARA_REMOVER = 5

logging.basicConfig(
    filename="acessos.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


def db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


@app.before_request
def registrar_requisicao():
    logging.info(f"{request.remote_addr} {request.method} {request.path}")


@app.after_request
def aplicar_headers_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


def autenticar_admin():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    cur = db().cursor(dictionary=True)
    cur.execute(
        "SELECT id, nivel_acesso FROM usuarios WHERE api_key = %s", (api_key,)
    )
    usuario = cur.fetchone()
    cur.close()
    return usuario


@app.route("/api/usuarios/buscar")
def buscar():
    nome = request.args.get("nome", "")
    cur = db().cursor(dictionary=True)
    cur.execute(
        "SELECT id, nome, email FROM usuarios WHERE nome LIKE %s",
        (f"%{nome}%",),
    )
    return jsonify(cur.fetchall())


@app.route("/perfil")
def perfil():
    nome_usuario = escape(request.args.get("u", ""))
    return f"<h1>Bem-vindo, {nome_usuario}</h1>"


@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
def remover(uid):
    admin = autenticar_admin()
    if admin is None:
        return jsonify({"erro": "nao autenticado"}), 401
    if admin["nivel_acesso"] < NIVEL_PARA_REMOVER:
        return jsonify({"erro": "acesso negado"}), 403

    con = db()
    cur = con.cursor()
    cur.execute("SELECT id FROM usuarios WHERE id = %s", (uid,))
    if cur.fetchone() is None:
        cur.close()
        con.close()
        return jsonify({"erro": "usuario nao encontrado"}), 404

    cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"removido": uid}), 200


@app.route("/api/relatorio")
def relatorio():
    try:
        cur = db().cursor()
        cur.execute("SELECT * FROM tabela_inexistente")
        return jsonify(cur.fetchall())
    except Exception:
        app.logger.exception("erro ao gerar relatorio")
        return jsonify({"erro": "erro interno"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5005)

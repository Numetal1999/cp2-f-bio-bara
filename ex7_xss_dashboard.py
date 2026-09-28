from flask import Flask, render_template_string

from config import get_mongo_db

app = Flask(__name__)


# Jinja2 escapa por padrao; um |safe mal colocado desliga esse escape e o navegador volta a interpretar aspas e tags.
TEMPLATE_SEGURO = """
<!doctype html>
<html>
<head><title>Dashboard de incidentes</title></head>
<body>
<h1>Incidentes</h1>
<table border="1">
<tr><th>Titulo</th><th>Icone</th></tr>
{% for incidente in incidentes %}
<tr>
  <td>{{ incidente.titulo }}</td>
  <td><img src="/icone.png" alt="{{ incidente.ativo }}"></td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

TEMPLATE_INSEGURO = """
<!doctype html>
<html>
<head><title>Dashboard inseguro (NAO USAR)</title></head>
<body>
<h1>Incidentes (sem escape)</h1>
<table border="1">
<tr><th>Titulo</th><th>Icone</th></tr>
{% for incidente in incidentes %}
<tr>
  <td>{{ incidente.titulo | safe }}</td>
  <td><img src="/icone.png" alt="{{ incidente.ativo | safe }}"></td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""


def preparar_mongo():
    db = get_mongo_db()
    db.incidentes.drop()
    db.incidentes.insert_many([
        {"titulo": "<script>alert('xss1')</script>", "ativo": "SRV-WEB01"},
        {"titulo": "Acesso suspeito", "ativo": "x\" onerror=\"alert('xss2')"},
    ])
    return db


@app.after_request
def aplicar_headers_seguranca(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.route("/dashboard")
def dashboard():
    db = get_mongo_db()
    incidentes = list(db.incidentes.find({}, {"_id": 0}))
    return render_template_string(TEMPLATE_SEGURO, incidentes=incidentes)


@app.route("/dashboard-inseguro")
def dashboard_inseguro():
    db = get_mongo_db()
    incidentes = list(db.incidentes.find({}, {"_id": 0}))
    return render_template_string(TEMPLATE_INSEGURO, incidentes=incidentes)


if __name__ == "__main__":
    preparar_mongo()
    app.run(debug=False, host="0.0.0.0", port=5002)

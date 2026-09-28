import requests

BASE = "http://localhost:5001"


def chamar(metodo, path, api_key=None):
    headers = {"X-API-Key": api_key} if api_key else {}
    return requests.request(metodo, f"{BASE}{path}", headers=headers)


def main():
    testes = [
        ("GET", "/api/incidentes/1", "key-ana-001", 200),
        ("GET", "/api/incidentes/1", "key-bruno-002", 403),
        ("GET", "/api/incidentes/1", None, 401),
        ("GET", "/api/incidentes/1", "key-inexistente", 401),
        ("GET", "/api/incidentes", "key-bruno-002", 200),
        ("DELETE", "/api/incidentes/2", "key-ana-001", 200),
        ("DELETE", "/api/incidentes/1", "key-bruno-002", 403),
        ("GET", "/api/incidentes/999", "key-ana-001", 404),
    ]
    for metodo, path, api_key, esperado in testes:
        r = chamar(metodo, path, api_key)
        status = "OK" if r.status_code == esperado else "FALHOU"
        print(f"{metodo:6s} {path:24s} key={str(api_key):18s} -> {r.status_code} (esperado {esperado}) [{status}]")


if __name__ == "__main__":
    main()

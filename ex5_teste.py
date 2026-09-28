import requests

BASE = "http://localhost:5000"


def main():
    r = requests.get(f"{BASE}/api/eventos", params={"ordenar_por": "sev", "ordem": "desc", "tamanho": 5})
    print(r.status_code, len(r.json()), "eventos ordenados por severidade")

    r = requests.get(f"{BASE}/api/eventos", params={"ordenar_por": "criado_em,(SELECT+1)", "ordem": "asc"})
    print(r.status_code, r.json())

    r = requests.get(f"{BASE}/api/eventos", params={"tamanho": "abc"})
    print(r.status_code, r.json())

    r = requests.get(f"{BASE}/api/eventos", params={"tamanho": "100000"})
    print(r.status_code, len(r.json()), "registros (teto do servidor)")


if __name__ == "__main__":
    main()

import time
import requests

BASE = "http://localhost:5004"


def simular_ip_normal():
    for _ in range(5):
        requests.get(f"{BASE}/api/ping")
        time.sleep(1)


def simular_ip_hostil():
    for i in range(60):
        rota = "/api/rota-inexistente" if i % 3 == 0 else "/api/ping"
        requests.get(f"{BASE}{rota}")


def main():
    simular_ip_normal()
    simular_ip_hostil()

    r = requests.post(f"{BASE}/api/analise-acessos")
    print(r.status_code, r.json())

    r = requests.get(f"{BASE}/api/ping")
    print(r.status_code, r.headers.get("Retry-After"), r.json())


if __name__ == "__main__":
    main()

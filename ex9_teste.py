import requests

BASE = "http://localhost:5004"


def acessar(ip, rota):
    return requests.get(f"{BASE}{rota}", headers={"X-Forwarded-For": ip})


def simular_ips_normais():
    for n in range(1, 7):
        for _ in range(5):
            acessar(f"10.0.0.{n}", "/api/ping")


def simular_ip_hostil():
    for i in range(60):
        rota = "/api/rota-inexistente" if i % 3 == 0 else "/api/ping"
        acessar("10.0.0.99", rota)


def main():
    simular_ips_normais()
    simular_ip_hostil()

    r = requests.post(f"{BASE}/api/analise-acessos")
    print(r.status_code, r.json())

    r = acessar("10.0.0.99", "/api/ping")
    print("IP hostil:", r.status_code, r.headers.get("Retry-After"), r.json())

    r = acessar("10.0.0.1", "/api/ping")
    print("IP normal:", r.status_code, r.json())


if __name__ == "__main__":
    main()

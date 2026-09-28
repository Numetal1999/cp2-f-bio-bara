from config import get_mysql_connection, get_mongo_db

ativos = [
    (1, "SRV-WEB01", "192.168.1.10", "alta"),
    (2, "PC-RH03", "192.168.1.45", "baixa"),
]

alertas = [
    (1, 1, "BRUTE_FORCE", "critica"),
    (2, 1, "PORT_SCAN", "alta"),
    (3, 2, "XSS", "media"),
]


def preparar_mysql(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS alertas")
    cur.execute("DROP TABLE IF EXISTS ativos")
    cur.execute(
        """
        CREATE TABLE ativos (
            id INT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            ip VARCHAR(45) UNIQUE NOT NULL,
            criticidade ENUM('baixa','media','alta') NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE alertas (
            id INT PRIMARY KEY,
            ativo_id INT NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            severidade VARCHAR(20) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ativo_id) REFERENCES ativos(id)
        )
        """
    )
    cur.executemany("INSERT INTO ativos (id, nome, ip, criticidade) VALUES (%s, %s, %s, %s)", ativos)
    cur.executemany("INSERT INTO alertas (id, ativo_id, tipo, severidade) VALUES (%s, %s, %s, %s)", alertas)
    conn.commit()
    cur.close()


def ler_com_join(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT al.tipo, al.severidade, at.nome, at.ip, at.criticidade
        FROM alertas al
        JOIN ativos at ON at.id = al.ativo_id
        """
    )
    linhas = cur.fetchall()
    cur.close()
    return linhas


def montar_documentos(linhas):
    documentos = []
    for linha in linhas:
        documentos.append({
            "tipo": linha["tipo"],
            "severidade": linha["severidade"],
            "ativo": {
                "nome": linha["nome"],
                "ip": linha["ip"],
                "criticidade": linha["criticidade"],
            },
        })
    return documentos


def main():
    conn = get_mysql_connection()
    preparar_mysql(conn)

    linhas = ler_com_join(conn)
    documentos = montar_documentos(linhas)

    db = get_mongo_db()
    db.alertas.drop()
    db.alertas.insert_many(documentos)

    total_mysql = len(alertas)
    total_mongo = db.alertas.count_documents({})
    status = "MIGRACAO INTEGRA" if total_mysql == total_mongo else "DIVERGENCIA"
    print(f"MySQL: {total_mysql} alertas | MongoDB: {total_mongo} documentos -> {status}")

    sem_join = list(db.alertas.find({"ativo.criticidade": "alta"}))
    print(f"Consulta sem JOIN: db.alertas.find({{'ativo.criticidade':'alta'}}) -> {len(sem_join)} documentos")


    # Ganho: leitura do alerta ja com os dados do ativo, sem JOIN.
    # Perda: dado duplicado em cada alerta; renomear o ativo exige update_many.

    conn.close()


if __name__ == "__main__":
    main()

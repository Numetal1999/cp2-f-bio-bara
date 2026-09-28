from datetime import datetime

from config import get_mysql_connection, get_mongo_db

usuarios = [
    (1, "ana", "ana@x.com", 5),
    (2, "bruno", "bruno@x.com", 2),
    (3, "caio", "caio@x.com", 1),
]

NIVEL_MINIMO_PARA_ALTERAR = 5


def preparar_mysql(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios")
    cur.execute(
        """
        CREATE TABLE usuarios (
            id INT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL,
            nivel_acesso INT NOT NULL
        )
        """
    )
    cur.executemany(
        "INSERT INTO usuarios (id, nome, email, nivel_acesso) VALUES (%s, %s, %s, %s)",
        usuarios,
    )
    conn.commit()
    cur.close()


def registrar_auditoria(mongo_db, quem, alvo, nivel_anterior, nivel_novo, resultado):
    mongo_db.auditoria.insert_one({
        "quem": quem,
        "alvo": alvo,
        "nivel_anterior": nivel_anterior,
        "nivel_novo": nivel_novo,
        "resultado": resultado,
        "timestamp": datetime.now(),
    })


def alterar_nivel(admin_id, alvo_id, novo_nivel, conn=None, mongo_db=None):
    conn_local = conn or get_mysql_connection()
    mongo_local = mongo_db or get_mongo_db()

    cur = conn_local.cursor(dictionary=True)

    try:
        if admin_id == alvo_id:
            registrar_auditoria(mongo_local, admin_id, alvo_id, None, novo_nivel, "RECUSADO")
            return {"ok": False, "motivo": "auto-promocao nao permitida"}

        cur.execute("SELECT nivel_acesso FROM usuarios WHERE id = %s", (admin_id,))
        admin = cur.fetchone()
        if admin is None or admin["nivel_acesso"] < NIVEL_MINIMO_PARA_ALTERAR:
            registrar_auditoria(mongo_local, admin_id, alvo_id, None, novo_nivel, "RECUSADO")
            return {"ok": False, "motivo": "admin sem privilegio suficiente"}

        cur.execute("SELECT nivel_acesso FROM usuarios WHERE id = %s FOR UPDATE", (alvo_id,))
        alvo = cur.fetchone()
        if alvo is None:
            registrar_auditoria(mongo_local, admin_id, alvo_id, None, novo_nivel, "RECUSADO")
            return {"ok": False, "motivo": "alvo inexistente"}

        nivel_anterior = alvo["nivel_acesso"]

        cur.execute("UPDATE usuarios SET nivel_acesso = %s WHERE id = %s", (novo_nivel, alvo_id))
        conn_local.commit()

        registrar_auditoria(mongo_local, admin_id, alvo_id, nivel_anterior, novo_nivel, "SUCESSO")
        return {"ok": True, "nivel_anterior": nivel_anterior, "nivel_novo": novo_nivel}

    except Exception:
        conn_local.rollback()
        registrar_auditoria(mongo_local, admin_id, alvo_id, None, novo_nivel, "RECUSADO")
        raise
    finally:
        cur.close()


def main():
    conn = get_mysql_connection()
    mongo_db = get_mongo_db()

    preparar_mysql(conn)
    mongo_db.auditoria.drop()

    print(alterar_nivel(1, 2, 4, conn, mongo_db))
    print(alterar_nivel(2, 3, 5, conn, mongo_db))
    print(alterar_nivel(1, 1, 9, conn, mongo_db))
    print(alterar_nivel(1, 99, 3, conn, mongo_db))

    total_auditoria = mongo_db.auditoria.count_documents({})
    total_recusas = mongo_db.auditoria.count_documents({"resultado": "RECUSADO"})
    print(f"Trilha de auditoria ao final: {total_auditoria} documentos")
    print(f"db.auditoria.count_documents({{'resultado':'RECUSADO'}}) -> {total_recusas}")

    conn.close()


if __name__ == "__main__":
    main()

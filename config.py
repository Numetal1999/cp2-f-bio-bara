import os


MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "database": os.environ.get("MYSQL_DATABASE", "seguranca"),
}

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.environ.get("MONGO_DB", "seguranca")


def get_mysql_connection():
    import mysql.connector
    return mysql.connector.connect(**MYSQL_CONFIG)


def get_mongo_db():
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB_NAME]

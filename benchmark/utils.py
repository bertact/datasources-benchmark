import requests
import psycopg2
from pymongo import MongoClient


def elasticsearch_connection():
    try:
        conn_es = requests.get("http://elasticsearch-db:9200")
        if conn_es.status_code == 200:
            print("Connected to ES DB")
            return conn_es
        else:
            print(f"Can't connect to ES DB, status code: {conn_es.status_code}")
    except Exception as e:
        print(f"Can't connect to ES DB, error: {e}")


def mongo_connection():
    try:
        conn_mongo = MongoClient(
            "mongo-db", 27017, username="admin", password="password"
        )
        print("Connected to Mongo DB")
        return conn_mongo
    except Exception as e:
        print(f"Can't connect to Mongo DB, error: {e}")


def postgres_connection():
    try:
        conn_postgres = psycopg2.connect(
            dbname="benchmark_postgres",
            user="postgres",
            host="postgresql-db",
            password="password",
            port=5432,
        )
        print("Connected to Postgres DB")
        return conn_postgres
    except Exception as e:
        print(f"Can't connect to Postgres DB, error: {e}")

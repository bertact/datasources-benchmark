import psycopg2
from pymongo import MongoClient
import requests

try:
    conn_postgres = psycopg2.connect(
        dbname="benchmark_postgres",
        user="postgres",
        host="postgresql-db",
        password="password",
        port=5432,
    )
    print("Connected to Postgres DB")
except Exception as e:
    print("Can't connect to Postgres DB")
    print(f"{e}")


#cursor = conn_postgres.cursor()

# try:
#     cursor.execute(
#         """CREATE TABLE PROJECTS (
#             prj_id INTEGER,
#             "name" VARCHAR(45) NOT NULL,
#             budget INTEGER,
#             "end" DATE,
#             PRIMARY KEY(prj_id))"""
#     )
#     conn.commit()  # To commit changes to the disk

# except Exception as e:
#     cursor.execute("ROLLBACK")  # Rollback when fail
#     print(e)


try:
    conn_mongo = MongoClient("mongo-db", 27017, username="admin", password="password")
    print("Connected to Mongo DB")
except:
    print("Can't connect to Mongo DB")


try:
    conn_es = requests.get("http://elasticsearch-db:9200")
    if conn_es.status_code == 200:
        print("Connected to ES DB")
    else:
        print("Can't connect to ES DB")
        print(f"{conn_es.status_code}")
except requests.exceptions.RequestException as e:
    print("Can't connect to ES")
    print(f"{e}")

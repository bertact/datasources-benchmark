import psycopg2
from pymongo import MongoClient

try:
    conn_postgres = psycopg2.connect(
        dbname="benchmark_postgres",
        user="postgres",
        host="postgresql-db",
        password="password",
        port=5432,
    )
    print("Connected to Postgres DB")
except:
    print("Can't connect to Postgres DB")


cursor = conn_postgres.cursor()

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
    conn_mongo = MongoClient("mongo", 27017, username="admin", password="password")
    print("Connected to Mongo DB")
except:
    print("Can't connect to Mongo DB")

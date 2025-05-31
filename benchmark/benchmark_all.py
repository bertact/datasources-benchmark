import psycopg2

try:
    conn = psycopg2.connect(
        dbname="benchmark_postgres",
        user="postgres",
        host="postgresql-db",
        password="password",
        port=5432,
    )
    print("Connected to the DB")
except:
    print("Can't connect to the DB")

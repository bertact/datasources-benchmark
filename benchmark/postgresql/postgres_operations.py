from utils import postgres_connection
from psycopg2 import sql
from utils import create_stats_files, save_stats_to_file, get_docker_stats, total_stats
import time
import random


def get_max_id(postgres_conn, cursor, table_name):
    query = sql.SQL("SELECT MAX(emp_id) FROM {}").format(sql.Identifier(table_name))
    cursor.execute(query)
    max_id = cursor.fetchone()[0]
    postgres_conn.commit()
    print(f"Max id: {max_id}")
    return max_id


def select_by_id(
    postgres_conn, cursor, database_method, table_name, id, container_name
):
    query = sql.SQL("SELECT * FROM {} WHERE emp_id = %s").format(
        sql.Identifier(table_name)
    )

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    cursor.execute(query, (id,))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    result = cursor.fetchall()
    postgres_conn.commit()
    if result:
        stats = total_stats(
            table_name, len(result), end, start, stats_before, stats_after
        )
        save_stats_to_file(database_method, stats)


def execute_op_postgres(container_name):
    postgres_conn = postgres_connection()
    cursor = postgres_conn.cursor()

    # Get max id of the table
    max_id = get_max_id(postgres_conn, cursor, table_name="employees")

    # Select
    database_method = "postgres_select"
    create_stats_files(database_method)

    random_ids = random.sample(range(max_id + 1), k=50)
    for id in random_ids:
        select_by_id(
            postgres_conn,
            cursor,
            database_method,
            table_name="employees",
            id=id,
            container_name=container_name,
        )

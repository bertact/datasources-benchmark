from utils import postgres_connection
from psycopg2 import sql
from utils import (
    create_stats_files,
    save_stats_to_file,
    get_docker_stats,
    total_stats,
    load_dataset,
)
import time
import os
import csv
import subprocess


def wait_for_postgres(container_name):
    while True:
        result = subprocess.run(
            ["docker", "exec", container_name, "pg_isready"],
            capture_output=True,
        )
        if b"accepting connections" in result.stdout:
            break
        time.sleep(1)


def restart_postgres(container_name):
    print(f"Restarting container {container_name} to clear cache")
    subprocess.run(["docker", "restart", container_name])
    wait_for_postgres(container_name)


def reconnect_postgres():
    conn = postgres_connection()
    return conn, conn.cursor()


def insert(
    postgres_conn, cursor, database_method, table_name, file_path, container_name
):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line in reader:
            columns = line.keys()
            values = [line[col] for col in columns]
            placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))

            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                placeholders,
            )

            stats_before = get_docker_stats(container_name)
            start = time.perf_counter()
            cursor.execute(query, values)
            end = time.perf_counter()
            stats_after = get_docker_stats(container_name)

            postgres_conn.commit()
            stats = total_stats(table_name, 1, end, start, stats_before, stats_after)
            save_stats_to_file(database_method, stats)


def get_all_ids(postgres_conn, cursor, table_name, limit=None):
    query = sql.SQL("SELECT id FROM {} ORDER BY id").format(sql.Identifier(table_name))
    if limit:
        query += sql.SQL(" LIMIT %s")
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    ids = [row[0] for row in rows]
    postgres_conn.commit()

    third = len(ids) // 3
    select_ids = ids[:third]
    update_ids = ids[third : 2 * third]
    delete_ids = ids[2 * third :]
    return select_ids, update_ids, delete_ids


def get_cities(postgres_conn, cursor, table_name, limit=None):
    query = sql.SQL("SELECT DISTINCT city FROM {}").format(sql.Identifier(table_name))
    if limit:
        query += sql.SQL(" LIMIT %s")
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    ids = [row[0] for row in rows]
    postgres_conn.commit()
    print(f"Retrieved {len(ids)} cities from {table_name}")
    return ids


def select_by_id(
    postgres_conn, cursor, database_method, table_name, id, container_name
):
    query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table_name))

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


def select_filtering(
    postgres_conn, cursor, database_method, table_name, city, container_name
):
    query = sql.SQL(
        """
        SELECT * FROM {}
        WHERE city = %s
        AND name_prefix = 'Mr.'
        AND gender = 'M'
        AND salary > 65000
        AND age_in_company > 2
        AND year_of_joining > 2000
        """
    ).format(sql.Identifier(table_name))

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    cursor.execute(query, (city,))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    result = cursor.fetchall()
    postgres_conn.commit()
    if result:
        stats = total_stats(
            table_name, len(result), end, start, stats_before, stats_after
        )
        save_stats_to_file(database_method, stats)


def update_salary_by_id(
    postgres_conn, cursor, database_method, table_name, id, container_name
):
    query = sql.SQL("UPDATE {} SET salary = %s WHERE id = %s").format(
        sql.Identifier(table_name)
    )

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    cursor.execute(query, (65000, id))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    postgres_conn.commit()
    stats = total_stats(table_name, 1, end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def join_city_state(
    postgres_conn, cursor, database_method, main_table, join_table, container_name
):
    query = sql.SQL(
        """
        SELECT e.*, l.state AS state_long
        FROM {} AS e
        JOIN {} AS l
        ON e.state = l.abbreviation
        """
    ).format(sql.Identifier(main_table), sql.Identifier(join_table))

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    cursor.execute(query)
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    result = cursor.fetchall()
    postgres_conn.commit()

    stats = total_stats(main_table, len(result), end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def set_index(postgres_conn, cursor, use_index=True):
    if use_index:
        statements = [
            "DROP INDEX IF EXISTS idx_employees_city;",
            "DROP INDEX IF EXISTS idx_us_cities_city;",
            "CREATE INDEX idx_employees_city ON employees(city);",
            "CREATE INDEX idx_us_cities_city ON us_cities_states_counties(city);",
        ]
    else:
        statements = [
            "DROP INDEX IF EXISTS idx_employees_city;",
            "DROP INDEX IF EXISTS idx_us_cities_city;",
        ]

    for statement in statements:
        cursor.execute(statement)

    postgres_conn.commit()


def delete_by_id(
    postgres_conn, cursor, database_method, table_name, id, container_name
):
    query = sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(table_name))

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    cursor.execute(query, (id,))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    postgres_conn.commit()
    stats = total_stats(table_name, 1, end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def execute_op_postgres(container_name):
    postgres_conn = postgres_connection()
    cursor = postgres_conn.cursor()

    # Insert
    insert_path = "./datasets/insert"
    database_method = "postgres_insert_rows"
    create_stats_files(database_method)
    file_path = insert_path + "/employees.csv"
    insert(
        postgres_conn,
        cursor,
        database_method,
        table_name="employees",
        file_path=file_path,
        container_name=container_name,
    )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Get 30 ids from the table
    select_ids, update_ids, delete_ids = get_all_ids(
        postgres_conn, cursor, table_name="employees", limit=90
    )

    # # Select
    database_method = "postgres_select"
    create_stats_files(database_method)

    for id in select_ids:
        select_by_id(
            postgres_conn,
            cursor,
            database_method,
            table_name="employees",
            id=id,
            container_name=container_name,
        )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Get 30 cities from the table
    list_cities = get_cities(postgres_conn, cursor, table_name="employees", limit=30)

    # Select
    database_method = "postgres_filter"
    create_stats_files(database_method)

    for city in list_cities:
        select_filtering(
            postgres_conn,
            cursor,
            database_method,
            table_name="employees",
            city=city,
            container_name=container_name,
        )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Update
    database_method = "postgres_update"
    create_stats_files(database_method)
    for id in update_ids:
        update_salary_by_id(
            postgres_conn,
            cursor,
            database_method,
            table_name="employees",
            id=id,
            container_name=container_name,
        )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Join without indexes
    set_index(postgres_conn, cursor, use_index=False)
    database_method = "postgres_join_no_index"
    create_stats_files(database_method)
    for _ in range(30):
        join_city_state(
            postgres_conn,
            cursor,
            database_method,
            main_table="employees",
            join_table="state_abbrevs",
            container_name=container_name,
        )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Join with indexes
    database_method = "postgres_join_index"
    create_stats_files(database_method)
    for i in range(30):
        set_index(postgres_conn, cursor, use_index=True)
        join_city_state(
            postgres_conn,
            cursor,
            database_method,
            main_table="employees",
            join_table="state_abbrevs",
            container_name=container_name,
        )

    restart_postgres(container_name)
    postgres_conn, cursor = reconnect_postgres()

    # Delete
    database_method = "postgres_delete"
    create_stats_files(database_method)
    for id in delete_ids:
        delete_by_id(
            postgres_conn,
            cursor,
            database_method,
            table_name="employees",
            id=id,
            container_name=container_name,
        )

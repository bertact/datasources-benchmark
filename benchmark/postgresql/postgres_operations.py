from utils import postgres_connection
from psycopg2 import sql
import time
from pathlib import Path
import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean


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


def run_parallel(worker_fn, work_items, csv_path: Path, max_workers: int = 16):

    t0 = time.perf_counter()
    print(f"Launching {len(work_items)} tasks on {max_workers} workers …")

    rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future = {executor.submit(worker_fn, item): item for item in work_items}
        for fut in as_completed(future):
            try:
                rows.append(fut.result())
            except Exception as exc:
                print(f"Task {future[fut]} failed: {exc}")

    elapsed = time.perf_counter() - t0
    print(f"All tasks done in {elapsed:,.2f}s")

    if rows:
        csv_path.parent.mkdir(exist_ok=True, parents=True)
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"Wrote per-operation metrics → {csv_path}")

        avg_rt = mean(r["duration_ms"] for r in rows)
        print(f"Avg. response time: {avg_rt:.2f} ms across {len(rows)} ops")


def insert(line, table_name):
    postgres_conn, cursor = reconnect_postgres()

    columns = list(line.keys())
    values = [line[col] for col in columns]

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() * len(columns)),
    )

    start = time.perf_counter()
    cursor.execute(query, values)
    end = time.perf_counter()
    postgres_conn.commit()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def get_all_ids(table_name, limit=None):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL("SELECT DISTINCT id FROM {} ORDER BY id").format(
        sql.Identifier(table_name)
    )
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

    cursor.close()
    postgres_conn.close()

    return select_ids, update_ids, delete_ids


def get_cities(table_name, limit=None):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL("SELECT DISTINCT city FROM {}").format(sql.Identifier(table_name))
    if limit:
        query += sql.SQL(" LIMIT %s")
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    cities = [row[0] for row in rows]
    postgres_conn.commit()

    cursor.close()
    postgres_conn.close()

    return cities


def select_by_id(table_name, id):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table_name))

    start = time.perf_counter()
    cursor.execute(query, (id,))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def select_filtering(table_name, city):
    postgres_conn, cursor = reconnect_postgres()

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

    start = time.perf_counter()
    cursor.execute(query, (city,))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def update_salary_by_id(table_name, id):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL("UPDATE {} SET salary = %s WHERE id = %s").format(
        sql.Identifier(table_name)
    )

    start = time.perf_counter()
    cursor.execute(query, (65000, id))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def join_city_state(main_table, join_table):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL(
        """
        SELECT e.*, l.state AS state_long
        FROM {} AS e
        JOIN {} AS l
        ON e.state = l.abbreviation
        """
    ).format(sql.Identifier(main_table), sql.Identifier(join_table))

    start = time.perf_counter()
    cursor.execute(query)
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": main_table,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def set_index(use_index=True):
    postgres_conn, cursor = reconnect_postgres()

    if use_index:
        statements = [
            "DROP INDEX IF EXISTS idx_employees_city;",
            "DROP INDEX IF EXISTS idx_state_abbrevs;",
            "CREATE INDEX idx_employees_city ON employees(state);",
            "CREATE INDEX idx_state_abbrevs ON state_abbrevs(state);",
        ]
    else:
        statements = [
            "DROP INDEX IF EXISTS idx_employees_city;",
            "DROP INDEX IF EXISTS idx_state_abbrevs;",
        ]

    for statement in statements:
        cursor.execute(statement)

    postgres_conn.commit()

    cursor.close()
    postgres_conn.close()


def delete_by_id(table_name, id):
    postgres_conn, cursor = reconnect_postgres()

    query = sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(table_name))

    start = time.perf_counter()
    cursor.execute(query, (id,))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    cursor.close()
    postgres_conn.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": cursor.rowcount,
    }


def execute_op_postgres(container_name):
    # Insert
    insert_path = "./datasets/insert/employees.csv"
    result_file = "./performance_results/postgres/postgres_insert_rows.csv"

    with open(insert_path, newline="", encoding="utf-8") as f:
        work = [row for _, row in zip(range(1000), csv.DictReader(f))]

    def one(row):
        return insert(row, table_name="employees")

    run_parallel(one, work, Path(result_file), max_workers=8)

    restart_postgres(container_name)

    # Get 3000 ids from the table
    select_ids, update_ids, delete_ids = get_all_ids(table_name="employees", limit=3000)

    # Select
    result_file = "./performance_results/postgres/postgres_select.csv"

    def one(id):
        return select_by_id(
            table_name="employees",
            id=id,
        )

    run_parallel(one, select_ids, Path(result_file), max_workers=8)

    restart_postgres(container_name)

    # Get 1000 cities from the table
    list_cities = get_cities(table_name="employees", limit=1000)

    # Select filtering
    result_file = "./performance_results/postgres/postgres_select_filter.csv"

    def one(city):
        return select_filtering(
            table_name="employees",
            city=city,
        )

    run_parallel(one, list_cities, Path(result_file), max_workers=8)

    restart_postgres(container_name)

    # Update
    result_file = "./performance_results/postgres/postgres_update.csv"

    def one(id):
        return update_salary_by_id(
            table_name="employees",
            id=id,
        )

    run_parallel(one, update_ids, Path(result_file), max_workers=8)

    restart_postgres(container_name)

    # Join without indexes
    set_index(use_index=False)
    result_file = "./performance_results/postgres/postgres_join_no_index.csv"

    def one(count):
        return join_city_state(
            main_table="employees",
            join_table="state_abbrevs",
        )

    run_parallel(one, range(1000), Path(result_file), max_workers=4)

    restart_postgres(container_name)

    # Join with indexes
    set_index(use_index=True)
    result_file = "./performance_results/postgres/postgres_join_with_index.csv"

    def one(count):
        return join_city_state(
            main_table="employees",
            join_table="state_abbrevs",
        )

    run_parallel(one, range(1000), Path(result_file), max_workers=4)

    restart_postgres(container_name)

    # Delete
    result_file = "./performance_results/postgres/postgres_delete.csv"

    def one(id):
        return delete_by_id(
            table_name="employees",
            id=id,
        )

    run_parallel(one, delete_ids, Path(result_file), max_workers=8)

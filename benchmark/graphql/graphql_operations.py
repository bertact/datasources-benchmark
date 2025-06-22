import requests
import time
import csv
from pathlib import Path
from statistics import mean
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import postgres_connection, mongo_connection


def run_parallel(worker_fn, work_items, url, csv_path, max_workers=8):
    t0 = time.perf_counter()
    print(f"Launching {len(work_items)} GraphQL ID queries with {max_workers} workers…")

    rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker_fn, url, item): item for item in work_items}
        for fut in as_completed(futures):
            try:
                if fut.result():
                    rows.append(fut.result())
            except Exception as e:
                print(f"Query for id={futures[fut]} failed: {e}")

    elapsed = time.perf_counter() - t0
    print(f"All GraphQL tasks completed in {elapsed:.2f}s")

    # Write results to CSV
    if rows:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"Saved results: {csv_path}")
        avg = mean(r["duration_ms"] for r in rows if r["success"])
        print(f"Average response time: {avg:.2f} ms")


def get_all_ids(url, container, table_name="employees", limit=3000):
    query = """
    query($container: String!, $table: String!, $limit: Int!) {
      getAllIds(container: $container, table: $table, limit: $limit)
    }
    """
    variables = {"container": container, "table": table_name, "limit": limit}

    response = requests.post(url, json={"query": query, "variables": variables})

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    ids = data.get("data", {}).get("getAllIds")
    if not ids:
        raise Exception(f"No IDs returned: {data}")

    third = len(ids) // 3

    selectIds = ids[:third]
    updateIds = ids[third : 2 * third]
    deleteIds = ids[2 * third :]

    return selectIds, updateIds, deleteIds


def get_cities(url, container, table_name="employees", limit=1000):
    query = """
    query($container: String!, $table: String!, $limit: Int!) {
      getCities(container: $container, table: $table, limit: $limit)
    }
    """
    variables = {"container": container, "table": table_name, "limit": limit}

    response = requests.post(url, json={"query": query, "variables": variables})

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    cities = data.get("data", {}).get("getCities")
    if not cities:
        raise Exception(f"No cities returned: {data}")

    return cities


def postgres_set_index(use_index=True):
    postgres_conn = postgres_connection()
    cursor = postgres_conn.cursor()

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


def mongo_set_index(table_name="employees", join_table="state_abbrevs", use_index=True):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]
    collection_join = database[join_table]

    if use_index:
        collection.create_index("state", name="idx_employees_city")
        collection_join.create_index("state", name="idx_state_abbrevs")
    else:
        try:
            collection.drop_index("idx_employees_city")
            collection_join.drop_index("idx_state_abbrevs")
        except Exception:
            pass

    client.close()


def insert(url, container, row, table_name="employees"):
    columns = list(row.keys())

    mutation = """
    mutation($container: String!, $table: String!, $columns: [String!], $values: [String!]!) {
    insertData(container: $container, table: $table, columns: $columns, values: $values)
    }
    """

    variables = {
        "container": container,
        "table": table_name,
        "columns": columns,
        "values": list(row.values()),
    }

    start = time.perf_counter()
    response = requests.post(url, json={"query": mutation, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    success = data.get("data", {}).get("insertData")

    if success is True:
        return {
            "op": "insertData",
            "table": table_name,
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def select_by_id(url, id, container, table_name="employees"):
    query = """
    query($container: String!, $table: String!, $id: Int!) {
      selectById(container: $container, table: $table, id: $id)
    }
    """
    variables = {"container": container, "table": table_name, "id": id}

    start = time.perf_counter()
    response = requests.post(url, json={"query": query, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    success = data.get("data", {}).get("selectById")

    if success is True:
        return {
            "op": "selectById",
            "table": table_name,
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def select_filtering_by_city(url, container, city, table_name="employees"):
    query = """
    query($container: String!, $table: String!, $city: String!) {
      selectFiltering(container: $container, table: $table, city: $city)
    }
    """
    variables = {"container": container, "table": table_name, "city": city}

    start = time.perf_counter()
    response = requests.post(url, json={"query": query, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    success = response.json().get("data", {}).get("selectFiltering")

    if success is True:
        return {
            "op": "selectFiltering",
            "table": table_name,
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def update_by_id(url, id, container, table_name="employees"):
    mutation = """
    mutation($container: String!, $table: String!, $id: Int!) {
      updateSalaryById(container: $container, table: $table, id: $id)
    }
    """
    variables = {
        "container": container,
        "table": table_name,
        "id": id,
    }

    start = time.perf_counter()
    response = requests.post(url, json={"query": mutation, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    success = data.get("data", {}).get("updateSalaryById")

    if success is True:
        return {
            "op": "updateSalaryById",
            "table": table_name,
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def join_city_state(
    url, container, main_table="employees", join_table="state_abbreviations"
):
    query = """
    query($container: String!, $main_table: String!, $join_table: String!) {
      joinCityState(container: $container, main_table: $main_table, join_table: $join_table)
    }
    """
    variables = {
        "container": container,
        "main_table": main_table,
        "join_table": join_table,
    }

    start = time.perf_counter()
    response = requests.post(url, json={"query": query, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    success = response.json().get("data", {}).get("joinCityState")

    if success is True:
        return {
            "op": "joinCityState",
            "table": f"{main_table}+{join_table}",
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def delete_by_id(url, id, container, table_name="employees"):
    mutation = """
    mutation($container: String!, $table: String!, $id: Int!) {
      deleteById(container: $container, table: $table, id: $id)
    }
    """
    variables = {"container": container, "table": table_name, "id": id}

    start = time.perf_counter()
    response = requests.post(url, json={"query": mutation, "variables": variables})
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: {response.text}")

    data = response.json()
    success = data.get("data", {}).get("deleteById")

    if success is True:
        return {
            "op": "deleteById",
            "table": table_name,
            "duration_ms": round(duration_ms, 3),
            "success": success,
        }


def execute_op_graphql(container):
    url = "http://graphql-api:8000/graphql"

    # Insert
    insert_path = (
        "./datasets/insert/employees.csv"
        if container == "postgres"
        else "./datasets/insert/employees.json"
    )
    result_file = f"./performance_results/graphql/{container}_insert_rows.csv"

    with open(insert_path, newline="", encoding="utf-8") as f:
        work = [row for _, row in zip(range(1000), csv.DictReader(f))]

    def one(url, row):
        return insert(url, container, row)

    run_parallel(one, work, url, Path(result_file), max_workers=8)

    # Get ids
    selectIds, updateIds, deleteIds = get_all_ids(url, container)

    # Select
    result_file = f"./performance_results/graphql/graphql_{container}_select.csv"

    def one(url, id):
        return select_by_id(url, id, container)

    run_parallel(one, selectIds, url, Path(result_file), max_workers=8)

    # Get cities
    cities = get_cities(url, container)

    # Select filtering
    result_file = f"./performance_results/graphql/graphql_{container}_select_filter.csv"

    def one(url, city):
        return select_filtering_by_city(url, container, city)

    run_parallel(one, cities, url, Path(result_file), max_workers=8)

    # Update
    result_file = f"./performance_results/graphql/graphql_{container}_update.csv"

    def one(url, id):
        return update_by_id(url, id, container)

    run_parallel(one, updateIds, url, Path(result_file), max_workers=8)

    # Join no index
    if container == "postgres":
        postgres_set_index(use_index=False)
    elif container == "mongodb":
        mongo_set_index(use_index=False)

    result_file = f"./performance_results/graphql/graphql_{container}_join_no_index.csv"

    def one(url):
        return join_city_state(url, container)

    run_parallel(one, range(1000), url, Path(result_file), max_workers=8)

    # Join with index
    if container == "postgres":
        postgres_set_index(use_index=True)
    elif container == "mongodb":
        mongo_set_index(use_index=True)

    result_file = (
        f"./performance_results/graphql/graphql_{container}_join_with_index.csv"
    )

    def one(url):
        return join_city_state(url, container)

    run_parallel(one, range(1000), url, Path(result_file), max_workers=8)

    # Delete
    result_file = f"./performance_results/graphql/graphql_{container}_delete.csv"

    def delete_worker(url, id):
        return delete_by_id(url, id, container)

    run_parallel(delete_worker, deleteIds, url, Path(result_file), max_workers=8)

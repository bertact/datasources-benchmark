from utils import mongo_connection
from utils import (
    convert_csv_to_json_file,
)
import time
import subprocess
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
from pathlib import Path


def restart_mongodb(container_name):
    print(f"Restarting container {container_name} to clear cache")
    subprocess.run(["docker", "restart", container_name])
    time.sleep(5)


def reconnect_mongo():
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    return database


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


def insert(insert_row, table_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    start = time.perf_counter()
    collection.insert_one(insert_row)
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": 1,
    }


def get_all_ids(table_name, limit=None):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    result = collection.find({}, {"id"})
    result = result.limit(limit)
    ids = [doc["id"] for doc in result]

    third = len(ids) // 3
    select_ids = ids[:third]
    update_ids = ids[third : 2 * third]
    delete_ids = ids[2 * third :]

    client.close()

    return select_ids, update_ids, delete_ids


def select_by_id(table_name, id):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    start = time.perf_counter()
    result = list(collection.find({"id": id}))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": len(result),
    }


def get_cities(table_name, limit=None):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    cities = collection.distinct("city")
    if limit:
        cities = cities[:limit]

    client.close()
    return cities


def select_filtering(city, table_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    query = {
        "city": city,
        "name_prefix": "Mr.",
        "gender": "M",
        "salary": {"$gt": 65000},
        "age_in_company": {"$gt": 2},
        "year_of_joining": {"$gt": 2000},
    }

    start = time.perf_counter()
    result = list(collection.find(query))
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": len(result),
    }


def update_salary_by_id(id, table_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    start = time.perf_counter()
    collection.update_one({"id": id}, {"$set": {"salary": 65000}})
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": None,
    }


def set_index(table_name, use_index=True):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    if use_index:
        collection.create_index("city", name="idx_employees_city")
    else:
        try:
            collection.drop_index("idx_employees_city")
        except Exception:
            pass

    client.close()


def join_city_state(table_name, join_table):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    start = time.perf_counter()

    result = list(
        collection.aggregate(
            [
                {
                    "$lookup": {
                        "from": join_table,
                        "localField": "state",
                        "foreignField": "abbreviation",
                        "as": "state_info",
                    }
                },
                {"$unwind": "$state_info"},
                {"$project": {"id": 1, "name": 1, "state": 1, "state_info.state": 1}},
            ]
        )
    )

    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": len(result),
    }


def delete_by_id(id, table_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database[table_name]

    start = time.perf_counter()
    collection.delete_one({"id": id})
    end = time.perf_counter()

    dur_ms = (end - start) * 1_000

    client.close()

    return {
        "op": "insert",
        "table": table_name,
        "duration_ms": round(dur_ms, 3),
        "rowcount": None,
    }


def execute_op_mongodb(container_name):
    # Insert
    insert_path = "./datasets/insert/employees.csv"
    json_path = convert_csv_to_json_file(insert_path)
    result_file = "./performance_results/mongo_insert_rows.csv"

    with open(json_path, encoding="utf-8") as f:
        work = [json.loads(line) for _, line in zip(range(1000), f) if line.strip()]

    def one(row):
        return insert(row, table_name="employees")

    run_parallel(one, work, Path(result_file), max_workers=8)

    restart_mongodb(container_name)

    # Get sample IDs
    select_ids, update_ids, delete_ids = get_all_ids(table_name="employees", limit=3000)

    # Select by ID
    result_file = "./performance_results/mongo_select.csv"

    def one(id):
        return select_by_id(table_name="employees", id=id)

    run_parallel(one, select_ids, Path(result_file), max_workers=8)

    restart_mongodb(container_name)

    # # Filtered select
    cities = get_cities(table_name="employees", limit=1000)

    result_file = "./performance_results/mongo_select_filter.csv"

    def one(city):
        return select_filtering(city, table_name="employees")

    run_parallel(one, cities, Path(result_file), max_workers=8)

    restart_mongodb(container_name)

    # Update
    result_file = "./performance_results/mongo_update.csv"

    def one(id):
        return update_salary_by_id(id, table_name="employees")

    run_parallel(one, update_ids, Path(result_file), max_workers=8)

    restart_mongodb(container_name)

    # Join without index
    set_index(table_name="employees", use_index=False)
    result_file = "./performance_results/mongo_join_no_index.csv"

    def one(int):
        return join_city_state(table_name="employees", join_table="state_abbrevs")

    run_parallel(one, range(1000), Path(result_file), max_workers=2)

    restart_mongodb(container_name)

    # Join with index
    set_index(table_name="employees", use_index=False)
    result_file = "./performance_results/mongo_join_with_index.csv"

    def one(int):
        return join_city_state(table_name="employees", join_table="state_abbrevs")

    run_parallel(one, range(1000), Path(result_file), max_workers=4)

    restart_mongodb(container_name)

    # Delete
    result_file = "./performance_results/mongo_join_with_index.csv"

    def one(id):
        return delete_by_id(id, table_name="employees")

    run_parallel(one, delete_ids, Path(result_file), max_workers=4)

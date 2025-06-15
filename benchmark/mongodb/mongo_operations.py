from utils import mongo_connection
from utils import (
    create_stats_files,
    save_stats_to_file,
    get_docker_stats,
    total_stats,
    convert_csv_to_json_file,
    load_dataset,
)
import time
import subprocess
import json


def restart_mongodb(container_name):
    print(f"Restarting container {container_name} to clear cache")
    subprocess.run(["docker", "restart", container_name])
    time.sleep(5)


def reconnect_mongo():
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    return database


def insert(collection, database_method, file_path, container_name):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            insert_row = json.loads(line)
            stats_before = get_docker_stats(container_name)
            start = time.perf_counter()
            collection.insert_one(insert_row)
            end = time.perf_counter()
            stats_after = get_docker_stats(container_name)

            stats = total_stats(
                collection.name, 1, end, start, stats_before, stats_after
            )
            save_stats_to_file(database_method, stats)


def get_all_ids(collection):
    result = collection.find({}, {"id"})
    result = result.limit(90)
    ids = [doc["id"] for doc in result]

    third = len(ids) // 3
    select_ids = ids[:third]
    update_ids = ids[third : 2 * third]
    delete_ids = ids[2 * third :]
    return select_ids, update_ids, delete_ids


def select_by_id(collection, database_method, id, container_name):
    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    result = list(collection.find({"id": id}))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)
    if result:
        stats = total_stats(
            table_name=collection.name,
            num_inserted=len(result),
            end=end,
            start=start,
            stats_before=stats_before,
            stats_after=stats_after,
        )
        save_stats_to_file(database_method, stats)


def get_cities(collection, limit=None):
    cities = collection.distinct("city")
    if limit:
        cities = cities[:limit]
    print(f"Retrieved {len(cities)} cities")
    return cities


def select_filtering(collection, database_method, city, container_name):
    query = {
        "city": city,
        "name_prefix": "Mr.",
        "gender": "M",
        "salary": {"$gt": 65000},
        "age_in_company": {"$gt": 2},
        "year_of_joining": {"$gt": 2000},
    }

    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    result = list(collection.find(query))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    if result:
        stats = total_stats(
            collection.name, len(result), end, start, stats_before, stats_after
        )
        save_stats_to_file(database_method, stats)


def update_salary_by_id(collection, database_method, id, container_name):
    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    collection.update_one({"id": id}, {"$set": {"salary": 65000}})
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    stats = total_stats(collection.name, 1, end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def set_index(collection, use_index=True):
    if use_index:
        collection.create_index("city", name="idx_employees_city")
        print("Index created.")
    else:
        try:
            collection.drop_index("idx_employees_city")
            print("Index dropped.")
        except Exception:
            pass


def join_city_state(database, database_method, container_name):
    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()

    result = list(
        database["employees"].aggregate(
            [
                {
                    "$lookup": {
                        "from": "state_abbrevs",
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
    stats_after = get_docker_stats(container_name)

    stats = total_stats("employees", len(result), end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def delete_by_id(collection, database_method, id, container_name):
    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    collection.delete_one({"id": id})
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)

    stats = total_stats(collection.name, 1, end, start, stats_before, stats_after)
    save_stats_to_file(database_method, stats)


def execute_op_mongodb(container_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database["employees"]

    # Insert
    insert_path = "./datasets/insert"
    database_method = "mongodb_insert_rows"
    create_stats_files(database_method)

    file_path = insert_path + "/employees.csv"
    json_path = convert_csv_to_json_file(file_path)
    insert(
        collection,
        database_method,
        file_path=json_path,
        container_name=container_name,
    )

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Get sample IDs
    select_ids, update_ids, delete_ids = get_all_ids(collection)

    # Select by ID
    database_method = "mongodb_select"
    create_stats_files(database_method)
    for id in select_ids:
        select_by_id(collection, database_method, id, container_name)

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Filtered select
    cities = get_cities(collection, limit=30)
    database_method = "mongodb_filter"
    create_stats_files(database_method)
    for city in cities:
        select_filtering(collection, database_method, city, container_name)

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Update
    database_method = "mongodb_update"
    create_stats_files(database_method)
    for id in update_ids:
        update_salary_by_id(collection, database_method, id, container_name)

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Join without index
    set_index(collection, use_index=False)
    database_method = "mongodb_join_no_index"
    create_stats_files(database_method)
    for _ in range(30):
        join_city_state(database, database_method, container_name)

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Join with index
    set_index(collection, use_index=True)
    database_method = "mongodb_join_index"
    create_stats_files(database_method)
    for _ in range(30):
        join_city_state(database, database_method, container_name)

    restart_mongodb(container_name)
    database = reconnect_mongo()
    collection = database["employees"]

    # Delete
    database_method = "mongodb_delete"
    create_stats_files(database_method)
    for id in delete_ids:
        delete_by_id(collection, database_method, id, container_name)

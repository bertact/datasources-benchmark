from utils import mongo_connection
from utils import create_stats_files, save_stats_to_file, get_docker_stats, total_stats
import time
import random


def get_max_id(collection):
    result = collection.find_one(sort=[("emp_id", -1)])
    max_id = result["emp_id"] if result else 0
    print(f"Max id: {max_id}")
    return max_id


def select_by_id(collection, database_method, id, container_name):
    stats_before = get_docker_stats(container_name)
    start = time.perf_counter()
    result = list(collection.find({"emp_id": id}))
    end = time.perf_counter()
    stats_after = get_docker_stats(container_name)
    print(result)
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


def execute_op_mondodb(container_name):
    client = mongo_connection()
    database = client["benchmark_mongodb"]
    collection = database["employees"]

    # Get max id of the table
    max_id = get_max_id(collection)

    # Select
    database_method = "mondodb_select"
    create_stats_files(database_method)

    random_ids = random.sample(range(max_id + 1), k=50)
    for id in random_ids:
        select_by_id(
            collection,
            database_method,
            id=id,
            container_name=container_name,
        )

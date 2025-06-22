from utils import convert_csv_to_json_file
import time
from utils import get_docker_stats, save_stats_to_file, total_stats
import json


def create_collection(client, table_name):
    database = client["benchmark_mongodb"]
    collection = database[f"{table_name}"]
    print(f"Collection {table_name} created in MongoDB")
    return collection


def insert_documents(table_name, collection, json_path, container_name):
    num_inserted = 0

    try:
        stats_before = get_docker_stats(container_name)
        start = time.perf_counter()

        with open(json_path, "r", encoding="utf-8") as f:
            batch = []
            for line in f:
                batch.append(json.loads(line))
                if len(batch) >= 5000:
                    collection.insert_many(batch)
                    num_inserted += len(batch)
                    batch = []
            if batch:
                collection.insert_many(batch)
                num_inserted += len(batch)

        end = time.perf_counter()
        stats_after = get_docker_stats(container_name)

        print(f"Inserted {num_inserted} JSON records")
        return total_stats(
            table_name, num_inserted, end, start, stats_before, stats_after
        )

    except Exception as e:
        print(f"Error inserting into MongoDB collection {table_name}: {e}")
        return {
            "table_name": table_name,
            "num_documents": num_inserted,
            "client_response_time": 0,
            "total_cpu": 0,
            "system_cpu": 0,
            "memory_used_bytes": 0,
        }


def mongodb_setup_db(conn, file_path, table_name, container_name):
    collection = create_collection(conn, table_name)
    json_path = convert_csv_to_json_file(file_path)
    mongo_stats = insert_documents(table_name, collection, json_path, container_name)

    save_stats_to_file(database_method="mongodb", results_stats=mongo_stats)

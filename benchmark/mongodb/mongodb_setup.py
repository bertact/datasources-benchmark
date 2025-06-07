from utils import to_json
import time
from utils import get_docker_stats, save_stats_to_file


def create_collection(client, table_name):
    database = client["mongodb_benchmark"]
    collection = database[f"{table_name}"]
    return collection


def insert_documents(collection, df):
    data = to_json(df)

    if data:
        start = time.perf_counter()
        collection.insert_many(data)
        end = time.perf_counter()

        elapsed = end - start
        print(f"Inserted {len(data)} documents to MongoDB in {elapsed:.2f} seconds")

        return len(data), elapsed
    return 0, 0


def mongodb_setup_db(conn, table_name, df, container_name):
    collection = create_collection(conn, table_name)
    num_inserted, elapsed = insert_documents(collection, df)
    container_stats = get_docker_stats(container_name)

    mongo_stats = {
        "table_name": table_name,
        "num_documents": num_inserted,
        "client_response_time": elapsed,
        **container_stats,
    }

    save_stats_to_file(database_method="mongo_insert", results_stats=mongo_stats)

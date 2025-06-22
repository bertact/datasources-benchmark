import time
import pandas as pd
from utils import get_docker_stats, save_stats_to_file, total_stats


def map_dtype_to_postgres(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "TEXT"


def create_table(conn, table_name, file_path):
    cursor = conn.cursor()

    try:
        df = pd.read_csv(file_path, nrows=5000, parse_dates=True)
        columns = ", ".join(
            [
                f"{col} {map_dtype_to_postgres(dtype)}"
                for col, dtype in df.dtypes.items()
            ]
        )
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Table {table_name} has been created")
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Failed to create table {table_name}: {e}")


def insert_data(conn, table_name, file_path, container_name):
    cursor = conn.cursor()

    try:

        with open(file_path, "r", encoding="utf-8") as f:
            num_inserted = sum(1 for _ in f) - 1
            f.seek(0)

            stats_before = get_docker_stats(container_name)

            start = time.perf_counter()
            cursor.copy_expert(
                f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER ','", f
            )
            conn.commit()
            end = time.perf_counter()

            stats_after = get_docker_stats(container_name)

            print(f"Data from file inserted to postgres table {table_name}")
            return total_stats(
                table_name, num_inserted, end, start, stats_before, stats_after
            )
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error inserting in postgrestable {table_name}: {e}")
        return {
            "table_name": table_name,
            "num_documents": 0,
            "client_response_time": 0,
            "total_cpu": 0,
            "system_cpu": 0,
            "memory_used_bytes": 0,
        }


def postgresql_setup_db(conn, file_path, table_name, container_name):
    create_table(conn, table_name, file_path)
    postgres_stats = insert_data(conn, table_name, file_path, container_name)

    save_stats_to_file(database_method="postgres", results_stats=postgres_stats)

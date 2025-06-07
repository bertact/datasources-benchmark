import time
from utils import get_docker_stats


def create_table(conn, table_name, df):
    cursor = conn.cursor()

    columns = ", ".join([f"{col} VARCHAR" for col in df.columns])
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"

    try:
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Table {table_name} has been created")
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(e)


def insert_data(conn, table_name, df):
    cursor = conn.cursor()

    insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(df.columns))})"
    data = df.values.tolist()

    try:
        start = time.perf_counter()
        cursor.executemany(insert_query, data)
        end = time.perf_counter()

        elapsed = end - start

        conn.commit()
        print(
            f"Data from file inserted to postgres table {table_name} in {elapsed:.2f} seconds"
        )
        return len(data), elapsed
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(e)


def postgresql_setup_db(conn, table_name, df, container_name):
    create_table(conn, table_name, df)
    num_inserted, elapsed = insert_data(conn, table_name, df)
    container_stats = get_docker_stats(container_name)

    return {
        "table_name": table_name,
        "num_documents": num_inserted,
        "client_response_time": elapsed,
        **container_stats,
    }

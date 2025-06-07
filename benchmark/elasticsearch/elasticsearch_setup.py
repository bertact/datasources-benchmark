from utils import to_json, flatten_file


def create_collection(client, table_name):
    print(client.list_database_names())
    database = client["mongodb_benchmark"]
    collection = database[f"{table_name}"]
    return collection


def insert_documents(df):
    json_data_file = to_json(df)
    flat = flatten_file(json_data_file)
    print(flat)


def elasticsearch_setup_db(df):
    # collection = create_collection(conn, table_name)
    insert_documents(df)

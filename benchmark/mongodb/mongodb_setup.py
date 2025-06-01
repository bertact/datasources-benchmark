def create_collection(client, table_name):
    print(client.list_database_names())
    database = client["mongodb_benchmark"]
    collection = database[f"{table_name}"]
    return collection


def insert_documents(collection, df):
    data = df.to_dict(orient="records")

    if data:
        collection.insert_many(data)
        print(f"Inserted {len(data)} documents")


def mongodb_setup_db(conn, table_name, df):
    collection = create_collection(conn, table_name)
    insert_documents(collection, df)

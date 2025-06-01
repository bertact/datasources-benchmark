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
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"Data from file inserted to table {table_name}")
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(e)


def postgresql_setup_db(conn, table_name, df):
    create_table(conn, table_name, df)
    insert_data(conn, table_name, df)

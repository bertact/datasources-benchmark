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


def postgresql_setup_db(conn, table_name, df):
    create_table(conn, table_name, df)

import os

from utils import load_dataset, postgres_connection, get_table_name
from postgresql.postgresql_setup import postgresql_setup_db


def main():

    datasets_path = "./datasets"

    for dataset in os.listdir(datasets_path):

        df = load_dataset(dataset, datasets_path)
        table_name = get_table_name(dataset)

        postgres_conn = postgres_connection()

        postgresql_setup_db(postgres_conn, table_name, df)


if __name__ == "__main__":
    main()

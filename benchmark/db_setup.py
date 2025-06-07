import os

from utils import (
    load_dataset,
    postgres_connection,
    get_table_name,
    mongo_connection,
    create_stats_files,
)
from postgresql.postgresql_setup import postgresql_setup_db
from mongodb.mongodb_setup import mongodb_setup_db
from elasticsearch.elasticsearch_setup import elasticsearch_setup_db


def main():

    datasets_path = "./datasets"

    # Create files
    for database in ["postgres", "mongo"]:
        create_stats_files(database_method=f"{database}_insert")

    for dataset in os.listdir(datasets_path):
        df = load_dataset(dataset, datasets_path)
        table_name = get_table_name(dataset)

        postgres_conn = postgres_connection()
        mongo_client = mongo_connection()

        postgresql_setup_db(
            postgres_conn,
            table_name,
            df,
            container_name="datasources-benchmark-postgresql-db-1",
        )

        mongodb_setup_db(
            mongo_client,
            table_name,
            df,
            container_name="datasources-benchmark-mongo-db-1",
        )


if __name__ == "__main__":
    main()

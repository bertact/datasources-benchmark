from postgresql.postgres_operations import execute_op_postgres
from mongodb.mongo_operations import execute_op_mongodb
from graphql.graphql_operations import execute_op_graphql


def main():
    # execute_op_postgres(container_name="datasources-benchmark-postgresql-db-1")
    # execute_op_mongodb(container_name="datasources-benchmark-mongo-db-1")
    execute_op_graphql(container="postgres")
    execute_op_graphql(container="mongodb")


if __name__ == "__main__":
    main()

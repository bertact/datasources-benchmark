from postgresql.postgres_operations import execute_op_postgres
from mongodb.mongo_operations import execute_op_mondodb


def main():
    execute_op_postgres(container_name="datasources-benchmark-postgresql-db-1")
    execute_op_mondodb(container_name="datasources-benchmark-postgresql-db-1")


if __name__ == "__main__":
    main()

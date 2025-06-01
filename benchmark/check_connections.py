from utils import elasticsearch_connection, mongo_connection, postgres_connection


def main():
    elasticsearch_connection()
    mongo_connection()
    postgres_connection()


if __name__ == "__main__":
    main()

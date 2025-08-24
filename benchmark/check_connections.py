from utils import mongo_connection, postgres_connection


def main():
    mongo_connection()
    postgres_connection()


if __name__ == "__main__":
    main()

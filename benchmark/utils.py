import requests
import psycopg2
from pymongo import MongoClient
import pandas as pd
import os
import docker
import csv


def elasticsearch_connection():
    try:
        conn_es = requests.get("http://elasticsearch-db:9200")
        if conn_es.status_code == 200:
            print("Connected to ES DB")
            return conn_es
        else:
            print(f"Can't connect to ES DB, status code: {conn_es.status_code}")
    except Exception as e:
        print(f"Can't connect to ES DB, error: {e}")


def mongo_connection():
    try:
        conn_mongo = MongoClient(
            "mongo-db", 27017, username="admin", password="password"
        )
        print("Connected to Mongo DB")
        return conn_mongo
    except Exception as e:
        print(f"Can't connect to Mongo DB, error: {e}")


def postgres_connection():
    try:
        conn_postgres = psycopg2.connect(
            dbname="benchmark_postgres",
            user="postgres",
            host="postgresql-db",
            password="password",
            port=5432,
        )
        print("Connected to Postgres DB")
        return conn_postgres
    except Exception as e:
        print(f"Can't connect to Postgres DB, error: {e}")


def load_dataset(path, datasets_path):
    if path.endswith(".csv"):
        file_path = os.path.join(datasets_path, path)
        return file_path, pd.read_csv(file_path)
    else:
        raise ValueError(f"File type not supported: {path}")


def get_table_name(dataset):
    return dataset.removesuffix(".csv")


def to_json(df):
    return df.to_dict(orient="records")


def flatten_json(context, old_json, new_json):
    for key in old_json.keys():
        if isinstance(old_json[key], dict):
            if context:
                flatten_json(context + "." + key, old_json, new_json)
            else:  # empty context
                flatten_json(key, old_json[key], new_json)
        else:
            if context:
                new_json[context + "." + key] = old_json[key]
            else:  # empty context
                new_json[key] = old_json[key]


def flatten_file(json_data_file):
    new_jsons = []
    for item in json_data_file:
        new_json = dict()
        flatten_json("", item, new_json)
        new_jsons.append(new_json)
    return new_jsons


def get_docker_stats(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)

        stats = container.stats(stream=False)

        cpu_total = stats["cpu_stats"]["cpu_usage"]["total_usage"]
        system_cpu = stats["cpu_stats"]["system_cpu_usage"]
        mem = stats["memory_stats"]["usage"]
        return {"cpu_total": cpu_total, "system_cpu": system_cpu, "memory": mem}
    except Exception as e:
        print("Failed to get Docker stats:", e)
        return {}


def create_stats_files(database_method):
    with open(f"{database_method}_performance.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "table_name",
                "num_documents",
                "client_response_time",
                "total_cpu",
                "system_cpu",
                "memory_used_bytes",
            ]
        )


def save_stats_to_file(database_method, results_stats):
    with open(f"{database_method}_performance.csv", "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results_stats.keys())
        writer.writerow(results_stats)

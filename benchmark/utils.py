import requests
import psycopg2
from pymongo import MongoClient
import pandas as pd
import os
import docker
import csv
import json

def mongo_connection():
    try:
        conn_mongo = MongoClient(
            "mongo-db", 27017, username="admin", password="password"
        )
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
        return conn_postgres
    except Exception as e:
        print(f"Can't connect to Postgres DB, error: {e}")


def load_dataset(path, datasets_path):
    if path.endswith(".csv"):
        file_path = os.path.join(datasets_path, path)
        table_name = path.removesuffix(".csv")
        return file_path, table_name
    else:
        raise ValueError(f"File type not supported: {path}")


def convert_csv_to_json_file(csv_path, chunksize=5000):
    json_path = csv_path.replace("csv", "json")
    with open(json_path, "w", encoding="utf-8") as outfile:
        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            records = chunk.to_dict(orient="records")
            for record in records:
                outfile.write(json.dumps(record) + "\n")
    print(f"CSV file {csv_path} converted to json")
    return json_path


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


def total_stats(table_name, num_inserted, end, start, stats_before, stats_after):
    elapsed = end - start
    cpu_delta = stats_after["cpu_total"] - stats_before["cpu_total"]
    system_delta = stats_after["system_cpu"] - stats_before["system_cpu"]
    memory_used = stats_after["memory"] - stats_before["memory"]

    cpu_count = os.cpu_count()
    cpu_percent = (cpu_delta / system_delta) * cpu_count * 100

    return {
        "table_name": table_name,
        "num_documents": num_inserted,
        "client_response_time": round(elapsed, 6),
        "total_cpu": cpu_delta,
        "system_cpu": system_delta,
        "cpu_percent": round(cpu_percent, 6),
        "memory_used_bytes": memory_used,
    }


def create_stats_files(database_method):
    with open(
        f"performance_results/{database_method}/dataset_insert_performance.csv", "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "table_name",
                "num_documents",
                "client_response_time",
                "total_cpu",
                "system_cpu",
                "cpu_percent",
                "memory_used_bytes",
            ]
        )


def save_stats_to_file(database_method, results_stats):
    with open(
        f"performance_results/{database_method}/dataset_insert_performance.csv", "a", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=results_stats.keys())
        writer.writerow(results_stats)

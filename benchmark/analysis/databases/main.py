import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set(style="whitegrid")
plt.rcParams.update({"figure.max_open_warning": 0})

base_path = "../../performance_results"
databases = ["mongodb", "postgres"]
results = []

for db in databases:
    folder_path = os.path.join(base_path, db)
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            operation = filename.replace(f"{db}_", "").replace(".csv", "")
            df = pd.read_csv(os.path.join(folder_path, filename))
            df["database"] = db
            df["operation"] = operation
            results.append(df)

all_data = pd.concat(results, ignore_index=True)

summary_stats = (
    all_data.groupby(["database", "operation"])["duration_ms"]
    .agg(["count", "mean", "std", "min", "max", "median", "quantile"])
    .reset_index()
)

summary_stats.to_csv("summary_stats.csv", index=False)
print("Summary statistics saved to summary_stats.csv")


# histogram per operation per database
output_dir = "benchmark_plots"
os.makedirs(output_dir, exist_ok=True)

for operation in all_data["operation"].unique():
    plt.figure(figsize=(10, 6))
    subset = all_data[all_data["operation"] == operation]
    sns.histplot(
        data=subset, x="duration_ms", hue="database", bins=30, kde=False, element="step"
    )
    plt.title(f"Histogram of '{operation}' duration by database")
    plt.xlabel("Duration (ms)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{operation}_histogram.png"))
    plt.close()


# line plot
input_csv = "summary_stats.csv"

df = pd.read_csv(input_csv)
df = df[df["database"].isin(["postgres", "mongodb"])]

pivot = df.pivot(index="operation", columns="database", values="mean")

plt.figure(figsize=(10, 6))
plt.plot(
    pivot.index, pivot["postgres"], marker="o", label="PostgreSQL", color="steelblue"
)
plt.plot(pivot.index, pivot["mongodb"], marker="o", label="MongoDB", color="seagreen")

plt.title("Raw Operation Mean Time")
plt.xlabel("Operation")
plt.ylabel("Mean Execution Time (ms)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "raw_ops_lineplot.png"))
plt.close()

# line plot avoid joins
input_csv = "summary_stats.csv"

df = pd.read_csv(input_csv)
df = df[df["database"].isin(["postgres", "mongodb"])]
df = df[
    df["operation"].isin(["delete", "insert_rows", "select_filter", "select", "update"])
]

pivot = df.pivot(index="operation", columns="database", values="mean")
print(pivot)

plt.figure(figsize=(10, 6))
plt.plot(
    pivot.index, pivot["postgres"], marker="o", label="PostgreSQL", color="steelblue"
)
plt.plot(pivot.index, pivot["mongodb"], marker="o", label="MongoDB", color="seagreen")

plt.title("Raw Operation Mean Time")
plt.xlabel("Operation")
plt.ylabel("Mean Execution Time (ms)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "raw_ops_lineplot_no_joins.png"))
plt.close()
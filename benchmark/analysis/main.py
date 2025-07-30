import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# output_dir = "plots_comp"

# raw_stats = pd.read_csv("databases/summary_stats.csv")
# graphql_stats = pd.read_csv("graphql/summary_stats.csv")

# # Fix operation and db columns if necessary
# for df in [raw_stats, graphql_stats]:
#     df["operation"] = df["operation"].str.lower()
#     df["database"] = df["database"].str.lower()


# # Pivot for easier diff calculation
# def pivot_diff(df, label):
#     pivot = df.pivot(index="operation", columns="database", values="mean").reset_index()
#     pivot["delta_postgres_minus_mongo"] = pivot["postgres"] - pivot["mongodb"]
#     pivot["source"] = label
#     return pivot[["operation", "delta_postgres_minus_mongo", "source"]]


# raw_delta = pivot_diff(raw_stats, "Raw DB")
# graphql_delta = pivot_diff(graphql_stats, "GraphQL")

# # Combine for plotting
# combined = pd.concat([raw_delta, graphql_delta])

# # Plot setup
# plt.figure(figsize=(10, 6))
# sns.barplot(data=combined, x="operation", y="delta_postgres_minus_mongo", hue="source")
# plt.axhline(0, color="black", linestyle="--")
# plt.title("Difference in Avg Duration (Postgres - MongoDB) per Operation")
# plt.ylabel("Δ Avg Duration (ms)")
# plt.xlabel("Operation")
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.savefig(os.path.join(output_dir, "raw_ops_lineplot_no_joins.png"))
# plt.savefig("graphql_vs_raw_comparison.png")
# plt.show()


df_raw = pd.read_csv("databases/summary_stats.csv")
df_graphql = pd.read_csv("graphql/summary_stats.csv")

common_ops = set(df_raw['operation']).intersection(df_graphql['operation'])
df_raw = df_raw[df_raw['operation'].isin(common_ops)]
df_graphql = df_graphql[df_graphql['operation'].isin(common_ops)]

df_merged = pd.merge(
    df_raw,
    df_graphql,
    on=["database", "operation"],
    suffixes=("_raw", "_graphql")
)

df_merged["slowdown"] = df_merged["mean_graphql"] / df_merged["mean_raw"]

plt.figure(figsize=(12, 6))
sns.barplot(
    data=df_merged,
    x="operation",
    y="slowdown",
    hue="database",
    palette="Set2"
)
plt.title("GraphQL Overhead: Slowdown Factor per Operation")
plt.ylabel("Slowdown Factor (GraphQL / Raw)")
plt.xlabel("Operation")
plt.axhline(1, color='gray', linestyle='--')
plt.legend(title="Database")
plt.tight_layout()

plt.savefig("plots_comp/graphql_vs_raw.png")
plt.close()

print(df_merged.groupby("database")["slowdown"].mean())

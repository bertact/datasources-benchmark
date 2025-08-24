import os

base_path = "benchmark_plots"
file_to_delete = os.path.join(base_path, "boxplot_operations.png")
try:
    for filename in os.listdir(base_path):
        full_path = os.path.join(base_path, filename)
        os.remove(full_path)
    # os.remove(file_to_delete)
    # print(f"Deleted {file_to_delete}")
except PermissionError as e:
    print(f"Could not delete {filename}: {e}")

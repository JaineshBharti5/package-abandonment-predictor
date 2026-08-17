import json
from pathlib import Path
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("PackageMerge").getOrCreate()

def load_json_dir(folder):
    records = []
    for f in Path(folder).glob("*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["package"] = f.stem
        records.append(data)
    return pd.DataFrame(records)

npm_pd = load_json_dir("data/raw/npm")
gh_pd = load_json_dir("data/raw/github")

print(f"npm records: {len(npm_pd)}")
print(f"github records: {len(gh_pd)}")

# flatten nested github fields (from the GraphQL response)
gh_pd["stars"] = gh_pd["stargazerCount"]
gh_pd["forks"] = gh_pd["forkCount"]
gh_pd["last_push_date"] = gh_pd["pushedAt"]
gh_pd["open_issues"] = gh_pd["issues"].apply(
    lambda x: x.get("totalCount") if isinstance(x, dict) else None
)
gh_pd["total_commits"] = gh_pd["defaultBranchRef"].apply(
    lambda x: (x or {}).get("target", {}).get("history", {}).get("totalCount")
    if isinstance(x, dict) else None
)
gh_flat_pd = gh_pd[["package", "stars", "forks", "last_push_date", "open_issues", "total_commits"]]

# hand off to Spark for the actual join/processing
npm_df = spark.createDataFrame(npm_pd.astype(str))
gh_df = spark.createDataFrame(gh_flat_pd.astype(str))

merged = npm_df.join(gh_df, on="package", how="inner")

print(f"merged records: {merged.count()}")
merged.printSchema()

Path("data/processed").mkdir(parents=True, exist_ok=True)
merged.toPandas().to_csv("data/processed/merged_dataset.csv", index=False)
print("Saved to data/processed/merged_dataset.csv")

spark.stop()

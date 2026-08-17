import json
import glob
import os
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("PackageAbandonmentFeatures").getOrCreate()


def load_json_files(pattern):
    results = []
    for path in glob.glob(pattern):
        with open(path, "r", encoding="utf-8") as f:
            results.append((path, json.load(f)))
    return results


def sum_downloads(downloads_field):
    if not downloads_field or not isinstance(downloads_field, dict):
        return 0.0
    daily = downloads_field.get("downloads")
    if not isinstance(daily, list):
        return 0.0
    total = 0
    for entry in daily:
        if isinstance(entry, dict):
            total += entry.get("downloads", 0) or 0
    return float(total)


def clean_npm_record(record):
    return {
        "name": record.get("name"),
        "version_count": int(record.get("version_count") or 0),
        "maintainer_count": int(record.get("maintainer_count") or 0),
        "last_publish_date": record.get("last_publish_date"),
        "total_downloads_1y": sum_downloads(record.get("downloads")),
    }


def github_key_from_path(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.replace("__", "/")


def clean_github_record(path, record):
    issues = record.get("issues") or {}
    branch = record.get("defaultBranchRef") or {}
    target = branch.get("target") or {}
    history = target.get("history") or {}
    nodes = history.get("nodes") or []

    authors = set()
    for n in nodes:
        author = (n.get("author") or {}).get("user")
        if author and author.get("login"):
            authors.add(author["login"])

    return {
        "name": github_key_from_path(path),
        "stars": int(record.get("stargazerCount") or 0),
        "forks": int(record.get("forkCount") or 0),
        "open_issues_count": int(issues.get("totalCount") or 0),
        "pushed_at": record.get("pushedAt"),
        "total_commit_count": int(history.get("totalCount") or 0),
        "recent_commit_sample_count": len(nodes),
        "recent_contributor_count": len(authors),
    }


npm_raw = load_json_files("data/raw/npm/*.json")
github_raw = load_json_files("data/raw/github/*.json")

npm_records = [clean_npm_record(r) for _, r in npm_raw]
github_records = [clean_github_record(p, r) for p, r in github_raw]

print("npm records:", len(npm_records))
print("github records:", len(github_records))

npm_names = {r["name"] for r in npm_records}
github_names = {r["name"] for r in github_records}
print("Matching names:", len(npm_names & github_names))

npm_df = spark.createDataFrame(npm_records)
github_df = spark.createDataFrame(github_records)

merged = npm_df.join(github_df, on="name", how="inner")

merged = merged.withColumn(
    "days_since_push",
    F.datediff(F.current_date(), F.to_date(F.substring(F.col("pushed_at"), 1, 10), "yyyy-MM-dd"))
).withColumn(
    "days_since_publish",
    F.datediff(F.current_date(), F.to_date(F.substring(F.col("last_publish_date"), 1, 10), "yyyy-MM-dd"))
)

merged = merged.withColumn(
    "is_unmaintained",
    F.when(F.col("days_since_push") >= 365, 1).otherwise(0)
)

print("Total joined records:", merged.count())
merged.groupBy("is_unmaintained").count().show()

merged.toPandas().to_csv("labeled_dataset.csv", index=False)

print("Saved labeled_dataset.csv")

spark.stop()

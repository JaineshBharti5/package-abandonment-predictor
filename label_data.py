from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder.appName("PackageLabeling")
    .master("local[2]")
    .config("spark.sql.execution.arrow.pyspark.enabled", "false")
    .getOrCreate()
)

df = spark.read.option("header", True).csv("data/processed/merged_dataset.csv")

# clean and parse ISO date strings (handles both with/without milliseconds)
for col_name, clean_name, ts_name in [
    ("last_push_date", "last_push_clean", "last_push_ts"),
    ("last_publish_date", "last_publish_clean", "last_publish_ts"),
]:
    df = df.withColumn(clean_name, F.regexp_replace(col_name, r"\.\d+Z$", ""))
    df = df.withColumn(clean_name, F.regexp_replace(clean_name, r"Z$", ""))
    df = df.withColumn(ts_name, F.to_timestamp(clean_name, "yyyy-MM-dd'T'HH:mm:ss"))

# days since last activity
df = df.withColumn("days_since_push", F.datediff(F.current_date(), F.col("last_push_ts")))
df = df.withColumn("days_since_publish", F.datediff(F.current_date(), F.col("last_publish_ts")))

# cast numeric columns properly
numeric_cols = ["version_count", "maintainer_count", "downloads", "stars", "forks", "open_issues", "total_commits"]
for c in numeric_cols:
    df = df.withColumn(c, F.col(c).cast("double"))

# label: unmaintained if no GitHub push in 365+ days
df = df.withColumn(
    "is_unmaintained",
    F.when(F.col("days_since_push") > 365, 1).otherwise(0)
)

print(f"Total records: {df.count()}")
print("Class balance:")
df.groupBy("is_unmaintained").count().show()

df.drop("last_push_clean", "last_publish_clean").toPandas().to_csv(
    "data/processed/labeled_dataset.csv", index=False
)
print("Saved to data/processed/labeled_dataset.csv")

spark.stop()

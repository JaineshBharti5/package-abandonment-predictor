import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

df = pd.read_csv("labeled_dataset.csv")

feature_cols = [
    "version_count",
    "maintainer_count",
    "total_downloads_1y",
    "stars",
    "forks",
    "open_issues_count",
    "total_commit_count",
    "recent_commit_sample_count",
    "recent_contributor_count",
    "days_since_publish",
]

df = df.dropna(subset=feature_cols + ["is_unmaintained"])

X = df[feature_cols]
y = df["is_unmaintained"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(classification_report(y_test, y_pred, target_names=["maintained", "unmaintained"]))

print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))

importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\nFeature importance:")
print(importances)

joblib.dump(model, "abandonment_model.pkl")
print("\nModel saved to abandonment_model.pkl")

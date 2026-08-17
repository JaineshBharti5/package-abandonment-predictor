import pandas as pd
import joblib
import streamlit as st

st.set_page_config(page_title="Package Abandonment Risk", layout="wide")

FEATURE_COLS = [
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


@st.cache_data
def load_data():
    df = pd.read_csv("labeled_dataset.csv")
    model = joblib.load("abandonment_model.pkl")
    df = df.dropna(subset=FEATURE_COLS).copy()
    df["risk_score"] = model.predict_proba(df[FEATURE_COLS])[:, 1]
    return df


df = load_data()

st.title("Open-Source Package Abandonment Risk Dashboard")
st.caption(f"{len(df)} packages analyzed")

search = st.text_input("Search package name")

filtered = df[df["name"].str.contains(search, case=False, na=False)] if search else df
filtered = filtered.sort_values("risk_score", ascending=False)

st.dataframe(
    filtered[["name", "risk_score", "stars", "total_downloads_1y", "days_since_publish", "is_unmaintained"]],
    use_container_width=True,
)

st.subheader("Risk score distribution")
st.bar_chart(df["risk_score"].value_counts(bins=10).sort_index())

st.subheader("Top 20 highest-risk packages (currently still marked maintained)")
st.caption("These are the early-warning packages — not abandoned yet, but the model flags them as high risk")
top_risk = df[df["is_unmaintained"] == 0].sort_values("risk_score", ascending=False).head(20)
st.dataframe(top_risk[["name", "risk_score", "stars", "days_since_publish"]], use_container_width=True)

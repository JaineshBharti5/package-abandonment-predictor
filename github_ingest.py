import os
import re
import json
import time
from pathlib import Path
import requests

# Token: pehle env var GITHUB_TOKEN check karega, warna github_token.txt file se padhega.
# (agar tumhara pehle wala script kisi aur naam se token store karta tha, yeh line badal dena)
TOKEN = os.environ.get("GITHUB_TOKEN") or Path("github_token.txt").read_text(encoding="utf-8-sig").strip()

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {TOKEN}"}

NPM_DIR = Path("data/raw/npm")
OUT_DIR = Path("data/raw/github")
OUT_DIR.mkdir(parents=True, exist_ok=True)
DONE_FILE = OUT_DIR / "_done.txt"

QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    forkCount
    pushedAt
    issues(states: OPEN) { totalCount }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100) {
            totalCount
            nodes {
              committedDate
              author { user { login } }
            }
          }
        }
      }
    }
  }
  rateLimit { remaining resetAt }
}
"""

def extract_owner_repo(npm_json):
    repo = npm_json.get("repository")
    url = repo.get("url") if isinstance(repo, dict) else repo
    if not url:
        return None
    m = re.search(r"github\.com[:/]+([^/]+)/([^/.]+)", url)
    if not m:
        return None
    return m.group(1), m.group(2).replace(".git", "")

def load_done():
    return set(DONE_FILE.read_text().splitlines()) if DONE_FILE.exists() else set()

def mark_done(pkg):
    with open(DONE_FILE, "a") as f:
        f.write(pkg + "\n")

def fetch_repo(owner, name):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"owner": owner, "name": name}},
        headers=HEADERS,
    )
    resp.raise_for_status()
    return resp.json()

def main():
    done = load_done()
    npm_files = sorted(NPM_DIR.glob("*.json"))
    print(f"Total packages: {len(npm_files)}, already done: {len(done)}")

    for i, npm_file in enumerate(npm_files, 1):
        pkg = npm_file.stem
        if pkg in done:
            continue

        npm_data = json.loads(npm_file.read_text())
        repo_info = extract_owner_repo(npm_data)
        if not repo_info:
            print(f"[{i}/{len(npm_files)}] {pkg}: no GitHub repo found, skipping")
            mark_done(pkg)
            continue

        owner, name = repo_info
        try:
            result = fetch_repo(owner, name)
        except requests.exceptions.RequestException as e:
            print(f"[{i}/{len(npm_files)}] {pkg}: request failed ({e}) — rerun script to resume")
            break

        if "errors" in result:
            msg = result["errors"][0].get("message")
            print(f"[{i}/{len(npm_files)}] {pkg}: {msg}")
            mark_done(pkg)
            continue

        remaining = result["data"]["rateLimit"]["remaining"]
        (OUT_DIR / f"{pkg}.json").write_text(json.dumps(result["data"]["repository"], indent=2))
        mark_done(pkg)
        print(f"[{i}/{len(npm_files)}] {pkg}: ok (quota remaining: {remaining})")

        if remaining < 50:
            reset_at = result["data"]["rateLimit"]["resetAt"]
            print(f"Quota low, stopping early. Resets at {reset_at} — rerun after that to resume.")
            break

    print("Done for this run.")

if __name__ == "__main__":
    main()

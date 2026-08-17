import requests
import json
import time
from pathlib import Path

OUTPUT_DIR = Path("data/raw/npm")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_URL = "https://registry.npmjs.org/{}"
DOWNLOADS_URL = "https://api.npmjs.org/downloads/range/last-year/{}"


def get_npm_metadata(package_name):
    response = requests.get(REGISTRY_URL.format(package_name))
    if response.status_code == 200:
        return response.json()
    return None


def get_npm_downloads(package_name):
    response = requests.get(DOWNLOADS_URL.format(package_name))
    if response.status_code == 200:
        return response.json()
    return None


def extract_features(metadata, downloads):
    versions = metadata.get("versions", {})
    time_data = metadata.get("time", {})
    version_list = list(versions.keys())
    latest_version = metadata.get("dist-tags", {}).get("latest")
    last_publish = time_data.get(latest_version) or time_data.get("modified")
    maintainers = metadata.get("maintainers", [])

    return {
        "name": metadata.get("name"),
        "version_count": len(version_list),
        "latest_version": latest_version,
        "last_publish_date": last_publish,
        "maintainer_count": len(maintainers),
        "repository": (metadata.get("repository").get("url") if isinstance(metadata.get("repository"), dict) else metadata.get("repository")),
        "license": metadata.get("license"),
        "downloads": downloads,
    }


def fetch_and_save(package_name):
    metadata = get_npm_metadata(package_name)
    if not metadata:
        return False

    downloads = get_npm_downloads(package_name)
    record = extract_features(metadata, downloads)

    safe_name = package_name.replace("/", "__")
    out_path = OUTPUT_DIR / f"{safe_name}.json"
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2)

    return True


def load_package_list(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def main():
    packages = load_package_list("package_list.txt")
    for i, pkg in enumerate(packages):
        success = fetch_and_save(pkg)
        status = "ok" if success else "failed"
        print(f"[{i + 1}/{len(packages)}] {pkg}: {status}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()

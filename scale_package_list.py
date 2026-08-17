import requests
import time

SEARCH_URL = "https://registry.npmjs.org/-/v1/search"

KEYWORDS = [
    "javascript",
    "typescript",
    "react",
    "vue",
    "angular",
    "css",
    "testing",
    "linter",
    "cli",
    "http-client",
    "build-tool",
    "webpack",
    "babel",
    "node",
    "express",
    "database",
    "logging",
    "utility",
    "graphql",
    "websocket",
]


def search_packages(keyword, size=100):
    params = {
        "text": f"keywords:{keyword}",
        "size": size,
        "popularity": 1.0,
    }
    response = requests.get(SEARCH_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return [obj["package"]["name"] for obj in data.get("objects", [])]
    return []


def build_package_list():
    all_names = set()
    for keyword in KEYWORDS:
        names = search_packages(keyword)
        all_names.update(names)
        print(f"{keyword}: +{len(names)} fetched, total unique so far {len(all_names)}")
        time.sleep(0.5)
    return sorted(all_names)


def main():
    packages = build_package_list()
    with open("package_list.txt", "w") as f:
        for name in packages:
            f.write(name + "\n")
    print(f"\nTotal packages saved to package_list.txt: {len(packages)}")


if __name__ == "__main__":
    main()

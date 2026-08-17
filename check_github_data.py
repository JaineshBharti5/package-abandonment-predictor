import json
import glob

paths = glob.glob("data/raw/github/*.json")
print("Total files:", len(paths))

for path in paths[:3]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("---", path, "---")
    print(data)
    print()

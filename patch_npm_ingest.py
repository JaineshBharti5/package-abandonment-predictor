from pathlib import Path

path = Path("npm_ingest.py")
content = path.read_text(encoding="utf-8")

old = 'metadata.get("repository", {}).get("url")'
new = (
    '(metadata.get("repository").get("url") '
    'if isinstance(metadata.get("repository"), dict) '
    'else metadata.get("repository"))'
)

if old in content:
    content = content.replace(old, new)
    path.write_text(content, encoding="utf-8")
    print("Patched successfully — repository field now handles both string and object formats.")
else:
    print("Exact line not found — file formatting might differ. Share the line around 'repository' and I'll help directly.")

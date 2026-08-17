from pathlib import Path

path = Path("github_ingest.py")
content = path.read_text(encoding="utf-8")

old = 'Path("github_token.txt").read_text().strip()'
new = 'Path("github_token.txt").read_text(encoding="utf-8-sig").strip()'

if old in content:
    content = content.replace(old, new)
    path.write_text(content, encoding="utf-8")
    print("Patched successfully — BOM characters will now be stripped from the token file.")
else:
    print("Exact line not found — file formatting might differ. Share the TOKEN line and I'll help directly.")

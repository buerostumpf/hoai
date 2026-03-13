#!/usr/bin/env python3
"""Split hoai2013.json into one JSON file per paragraph. Leaves original unchanged."""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
DATA_DIR = HERE.parent / "data"
SOURCE = DATA_DIR / "hoai2013.json"


def slug(s: str) -> str:
    """Safe filename from paragraph title: §18 Flächennutzungsplan -> 18_Flaechennutzungsplan."""
    s = s.strip()
    s = re.sub(r"^§\s*", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "_", s)
    return s[:80].strip("_") or "paragraph"


def main():
    with open(SOURCE, "r", encoding="utf-8") as f:
        data = json.load(f)
    hoai = data.get("hoai", "2013")
    paragraphs = data["paragraphs"]
    for i, para in enumerate(paragraphs):
        title = para.get("paragraph", "")
        name = slug(title) if title else f"paragraph_{i}"
        out = DATA_DIR / f"hoai2013_{name}.json"
        out.write_text(
            json.dumps({"hoai": hoai, "paragraphs": [para]}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(out.name)
    print(f"Wrote {len(paragraphs)} files.")


if __name__ == "__main__":
    main()

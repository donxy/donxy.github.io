#!/usr/bin/env python3
"""Build a reproducible, public cross-site manifest from authoritative source files.

Only records titles, links, counts and Git commit times. Never treats an article's
"information as of" date as its actual Git modification date.
"""
import argparse
import csv
import json
import re
import subprocess
from pathlib import Path


def last_git_edit(path: Path, repo: Path) -> str:
    if not path.is_file():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%cI", "--",
             str(path.relative_to(repo))],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()
    except (OSError, ValueError, subprocess.CalledProcessError):
        return ""


def md_title(path: Path) -> str:
    content = path.read_text(encoding="utf-8-sig")
    match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"\'')
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else path.stem


def recent_notes(content: Path, url: str, limit: int = 3,
                 include=None) -> list[dict]:
    repo = content.parent
    entries = []
    for file in content.rglob("*.md"):
        if file.name == "index.md" or (include and not include(file)):
            continue
        relative = file.relative_to(content).with_suffix("").as_posix()
        entries.append({
            "title": md_title(file),
            "url": url.rstrip("/") + "/" + relative,
            "updated_at": last_git_edit(file, repo),
        })
    entries.sort(key=lambda item: (item["updated_at"], item["url"]), reverse=True)
    return entries[:limit]


def generate(papers_csv: Path, issues_json: Path, ad_content: Path,
             rgbt_content: Path) -> dict:
    with papers_csv.open(encoding="utf-8-sig", newline="") as stream:
        papers = list(csv.DictReader(stream))
    issues = json.loads(issues_json.read_text(encoding="utf-8"))["issues"]
    ad_files = [p for p in ad_content.rglob("*.md") if p.name != "index.md"]
    dataset_files = [p for p in (rgbt_content / "datasets").glob("*.md")
                     if p.name != "index.md"]
    groups = {}
    for path in ad_files:
        parts = path.relative_to(ad_content).parts
        key = parts[0] if len(parts) > 1 else "timeline"
        groups[key] = groups.get(key, 0) + 1

    figure_entries = [{
        "title": it["title"],
        "url": "https://donxy.github.io/figure-teardown/" + it["page"],
        "updated_at": last_git_edit(issues_json.parent / it["page"],
                                    issues_json.parent.parent),
    } for it in issues]
    figure_entries.sort(key=lambda item: (item["updated_at"], item["url"]), reverse=True)

    return {
        "schema_version": 1,
        "sites": [
            {
                "id": "rgbt",
                "title": "RGB-T 论文笔记",
                "url": "https://donxy.github.io/rgbt-notes/",
                "source": "donxy/rgbt-notes + donxy/awesome-RGBT-ObjectDetection",
                "counts": {
                    "papers": len(papers),
                    "core": sum(p.get("list") == "core" for p in papers),
                    "appendix": sum(p.get("list") == "appendix" for p in papers),
                    "full_text": sum(p.get("notes_basis") == "full-text" for p in papers),
                    "datasets": len(dataset_files),
                },
                "recent": recent_notes(
                    rgbt_content, "https://donxy.github.io/rgbt-notes", include=lambda
                    p: p.relative_to(rgbt_content).parts[0] in ("core", "appendix")),
            },
            {
                "id": "figures",
                "title": "科研配图拆解",
                "url": "https://donxy.github.io/figure-teardown/",
                "source": "donxy/donxy.github.io",
                "counts": {"issues": len(issues)},
                "recent": figure_entries[:3],
            },
            {
                "id": "driving",
                "title": "无人驾驶技能树",
                "url": "https://donxy.github.io/autonomous-driving-notes/",
                "source": "donxy/autonomous-driving-notes",
                "counts": {"notes": len(ad_files), "groups": dict(sorted(groups.items()))},
                "recent": recent_notes(ad_content,
                                       "https://donxy.github.io/autonomous-driving-notes"),
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers-csv", type=Path, required=True)
    parser.add_argument("--issues-json", type=Path, required=True)
    parser.add_argument("--ad-content", type=Path, required=True)
    parser.add_argument("--rgbt-content", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("site-metadata.json"))
    args = parser.parse_args()
    result = generate(args.papers_csv, args.issues_json, args.ad_content,
                      args.rgbt_content)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", args.output, "with", len(result["sites"]), "sites")


if __name__ == "__main__":
    main()

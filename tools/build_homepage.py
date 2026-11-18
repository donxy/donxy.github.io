#!/usr/bin/env python3
"""Generate donxy.github.io homepage (index.html + og.png) from live data sources.

Sources of truth (numbers are never hand-written in the template):
  - papers.csv            ~/workspace/github-repos/awesome-RGBT-ObjectDetection/papers.csv
  - teardown issues       ~/workspace/figure-teardown/issues.json
  - AD notes count/groups ~/workspace/autonomous-driving-notes/quartz/content/
                          (same rule as that site's scripts/count-notes.mjs:
                           every .md under content/ except index.md)

Usage: python3 build_homepage.py [--out DIR]   (default: this script's folder)
"""
import argparse, csv, json, os, sys
from pathlib import Path

HOME = Path.home()
PAPERS_CSV = Path(os.environ.get("PAPERS_CSV", str(HOME / "workspace/github-repos/awesome-RGBT-ObjectDetection/papers.csv")))
ISSUES_JSON = Path(os.environ.get("ISSUES_JSON", str(Path(__file__).resolve().parent.parent / "figure-teardown/issues.json")))
AD_CONTENT = Path(os.environ.get("AD_CONTENT", str(HOME / "workspace/autonomous-driving-notes/quartz/content")))
TEMPLATE = Path(__file__).with_name("index.template.html")

AD_LABELS = [("history", "历史"), ("technology", "技术"), ("companies", "公司"),
             ("china", "中国市场"), ("regulation", "监管")]


def papers_stats():
    rows = list(csv.DictReader(open(PAPERS_CSV, encoding="utf-8-sig")))
    sub = {}
    for r in rows:
        if r["subsection"]:
            sub[r["subsection"]] = sub.get(r["subsection"], 0) + 1
    fl = {}
    for r in rows:
        fl[r["fusion_level"]] = fl.get(r["fusion_level"], 0) + 1
    return {
        "PAPERS_TOTAL": str(len(rows)),
        "PAPERS_CORE": str(sum(1 for r in rows if r["list"] == "core")),
        "PAPERS_APPENDIX": str(sum(1 for r in rows if r["list"] == "appendix")),
        "FULLTEXT": str(sum(1 for r in rows if r["notes_basis"] == "full-text")),
        "PIXEL": str(fl.get("pixel", 0)),
        "FEATURE": str(fl.get("feature", 0)),
        "DECISION": str(fl.get("decision", 0)),
        "NA_COUNT": str(fl.get("na", 0)),
        "SUB_ATT": str(sub.get("Attention, Transformers & Foundation Models", 0)),
        "SUB_DUAL": str(sub.get("Dual-Stream CNN & YOLO-Based Detectors", 0)),
        "SUB_MAMBA": str(sub.get("State-Space Models (Mamba)", 0)),
    }


def teardown_stats():
    data = json.load(open(ISSUES_JSON, encoding="utf-8"))
    issues = data["issues"]
    rows = []
    for it in issues:
        rows.append(
            '          <li><a href="/figure-teardown/{page}">'
            '<span class="no">{no}</span>'
            '<span class="tt">{title}</span>'
            '<span class="vn">{venue}</span></a></li>'.format(
                page=it["page"], no=it["no"], title=it["title"], venue=it["venue"]))
    return {"TEARDOWN_COUNT": str(len(issues)), "ISSUE_LIST": "\n".join(rows)}


def ad_stats():
    counts = {}
    total = 0
    for p in sorted(AD_CONTENT.rglob("*.md")):
        if p.name == "index.md":
            continue
        total += 1
        rel = p.relative_to(AD_CONTENT)
        key = rel.parts[0] if len(rel.parts) > 1 else "timeline"
        counts[key] = counts.get(key, 0) + 1
    chips = []
    for key, label in AD_LABELS:
        if key in counts:
            chips.append(f"          <span>{label} · {counts[key]}</span>")
    if counts.get("timeline"):
        chips.append(f"          <span>时间线 · {counts['timeline']}</span>")
    return {"AD_COUNT": str(total), "AD_GROUPS": "\n".join(chips)}


def make_og(out_png: Path):
    from PIL import Image, ImageDraw, ImageFont
    import glob
    def font(patterns, size):
        for pat in patterns:
            hits = sorted(glob.glob(pat, recursive=True))
            for h in hits:
                try:
                    return ImageFont.truetype(h, size)
                except Exception:
                    continue
        raise RuntimeError(f"no usable font in {patterns}")
    serif = lambda s: font(["/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
                            "/usr/share/fonts/**/NotoSerifCJK-Bold.ttc"], s)
    sans = lambda s: font(["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                           "/usr/share/fonts/**/NotoSansCJK-Regular.ttc"], s)
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (250, 248, 243))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([36, 36, W - 36, H - 36], radius=28, outline=(227, 222, 210), width=2)
    d.text((90, 120), "donxy", font=serif(120), fill=(14, 89, 65))
    d.text((94, 290), "研究笔记与视觉拆解", font=serif(54), fill=(28, 42, 38))
    d.text((94, 380), "RGBT 目标检测 · 科研配图 · 自动驾驶观察", font=sans(32), fill=(81, 98, 92))
    for i, c in enumerate([(14, 89, 65), (156, 90, 19), (46, 95, 122)]):
        x = 94 + i * 44
        d.ellipse([x, 480, x + 26, 506], fill=c)
    d.text((94, 540), "donxy.github.io", font=sans(26), fill=(81, 98, 92))
    img.save(out_png, "PNG")
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.out:
        out = Path(args.out)
    else:
        # In the repo the script lives in tools/ and generates at the repo root;
        # in the staging folder it generates beside itself.
        d = Path(__file__).parent
        out = d.parent if d.name == "tools" else d
    out.mkdir(parents=True, exist_ok=True)

    values = {}
    values.update(papers_stats())
    values.update(teardown_stats())
    values.update(ad_stats())

    html = TEMPLATE.read_text(encoding="utf-8")
    for k, v in values.items():
        html = html.replace("{{" + k + "}}", v)
    import re
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftovers:
        print("ERROR: unresolved tokens remain:", leftovers, file=sys.stderr)
        return 1
    (out / "index.html").write_text(html, encoding="utf-8")
    make_og(out / "og.png")
    print("generated:", out / "index.html")
    print("numbers:", {k: v for k, v in values.items() if k not in ("ISSUE_LIST", "AD_GROUPS")})
    return 0


if __name__ == "__main__":
    sys.exit(main())

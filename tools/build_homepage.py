#!/usr/bin/env python3
"""Generate donxy.github.io homepage (bilingual: index.html + en/index.html,
plus og.png for each) from live data sources.

Sources of truth (numbers are never hand-written in the template):
  - papers.csv            ~/workspace/github-repos/awesome-RGBT-ObjectDetection/papers.csv
  - teardown issues       ~/workspace/figure-teardown/issues.json
  - recent updates        tools/updates.json (editorial log next to this script;
                          each entry may carry text_en; a missing text_en makes
                          the English page fall back to the Chinese text and
                          lists the entry as pending translation)
  - UI strings            tools/i18n/zh.json, tools/i18n/en.json
                          (template tokens {{S.<key>}}; values may embed data
                          tokens such as {{PAPERS_TOTAL}}, resolved in pass 2)
  - AD notes count/groups ~/workspace/autonomous-driving-notes/quartz/content/
                          (same rule as that site's scripts/count-notes.mjs:
                           every .md under content/ except index.md)

Language rules (plan: ~/workspace/bilingual-sites/双语切换实施方案.md):
  - Chinese keeps the existing root path; English lives under en/.
  - Numbers come from the same data sources for both languages and are
    asserted equal before anything is written.
  - On the English page, recent-update links point to /en/ (the English
    homepage) until the notes sites ship their own English trees.

Usage: python3 build_homepage.py [--out DIR]   (default: repo root)
"""
import argparse, csv, json, re, sys
from pathlib import Path

HOME = Path.home()
PAPERS_CSV = HOME / "workspace/github-repos/awesome-RGBT-ObjectDetection/papers.csv"
ISSUES_JSON = HOME / "workspace/figure-teardown/issues.json"
UPDATES_JSON = Path(__file__).with_name("updates.json")
I18N_DIR = Path(__file__).with_name("i18n")
AD_CONTENT = HOME / "workspace/autonomous-driving-notes/repo/content"
TEMPLATE = Path(__file__).with_name("index.template.html")

LANGS = ("zh", "en")
HEADLINE_KEYS = ("PAPERS_TOTAL", "FULLTEXT", "TEARDOWN_COUNT", "AD_COUNT")

# AD content-dir key -> label per language (current five-line structure).
AD_LABELS = [
    ("history",    {"zh": "历史",       "en": "History"}),
    ("technology", {"zh": "技术",       "en": "Technology"}),
    ("market",     {"zh": "产业与市场", "en": "Industry & Market"}),
    ("companies",  {"zh": "公司",       "en": "Companies"}),
    ("regulation", {"zh": "安全与监管", "en": "Safety & Regulation"}),
]


def load_i18n(lang):
    return json.load(open(I18N_DIR / f"{lang}.json", encoding="utf-8"))


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


def updates_block(lang, pending):
    data = json.load(open(UPDATES_JSON, encoding="utf-8"))
    rows = []
    for u in data["updates"][:6]:
        text, href = u["text"], u["href"]
        if lang == "en":
            if u.get("text_en"):
                text = u["text_en"]
            else:
                pending.append(f"updates.json {u['date']}: missing text_en "
                               f"(English page falls back to Chinese)")
            # Notes sites have no English trees yet: link to the English
            # homepage for now (plan section 2.3).
            href = "/en/"
        rows.append(
            '          <li><span class="u-date">{date}</span>'
            '<i class="u-dot d-{line}"></i>'
            '<a href="{href}">{text}</a></li>'.format(
                date=u["date"], line=u["line"], href=href, text=text))
    return {"UPDATES": "\n".join(rows)}


def ad_stats(lang):
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
    for key, labels in AD_LABELS:
        if key in counts:
            label = labels[lang].replace("&", "&amp;")
            chips.append(f"          <span>{label} · {counts[key]}</span>")
    return {"AD_COUNT": str(total), "AD_GROUPS": "\n".join(chips)}


OG_TEXT = {
    "zh": {"title": "研究笔记与视觉拆解",
           "sub": "RGBT 目标检测 · 科研配图 · 自动驾驶观察"},
    "en": {"title": "Research Notes & Visual Teardowns",
           "sub": "RGBT Object Detection · Research Figures · Driving Notes"},
}


def make_og(out_png: Path, lang):
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
    d.text((94, 290), OG_TEXT[lang]["title"], font=serif(54), fill=(28, 42, 38))
    d.text((94, 380), OG_TEXT[lang]["sub"], font=sans(32), fill=(81, 98, 92))
    for i, c in enumerate([(14, 89, 65), (156, 90, 19), (46, 95, 122)]):
        x = 94 + i * 44
        d.ellipse([x, 480, x + 26, 506], fill=c)
    d.text((94, 540), "donxy.github.io", font=sans(26), fill=(81, 98, 92))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG")
    return out_png


def render(lang, template, pending):
    """Two passes: UI strings first (they may embed data tokens), then data."""
    html = template
    for key, val in load_i18n(lang).items():
        html = html.replace("{{S." + key + "}}", val)
    values = {}
    values.update(papers_stats())
    values.update(teardown_stats())
    values.update(ad_stats(lang))
    values.update(updates_block(lang, pending))
    for k, v in values.items():
        html = html.replace("{{" + k + "}}", v)
    leftovers = re.findall(r"\{\{[^}]+\}\}", html)
    if leftovers:
        print(f"ERROR[{lang}]: unresolved tokens remain:", leftovers, file=sys.stderr)
        return None, None
    return html, values


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

    template = TEMPLATE.read_text(encoding="utf-8")
    pending = []
    pages, numbers = {}, {}
    for lang in LANGS:
        html, values = render(lang, template, pending)
        if html is None:
            return 1
        pages[lang] = html
        numbers[lang] = {k: v for k, v in values.items()
                         if k not in ("ISSUE_LIST", "AD_GROUPS", "UPDATES")}

    # Both languages must show identical numbers (same data sources).
    for k in HEADLINE_KEYS:
        assert numbers["zh"][k] == numbers["en"][k], \
            f"count mismatch between languages: {k}"
    assert numbers["zh"] == numbers["en"], "number tables differ between languages"

    (out / "index.html").write_text(pages["zh"], encoding="utf-8")
    (out / "en").mkdir(parents=True, exist_ok=True)
    (out / "en" / "index.html").write_text(pages["en"], encoding="utf-8")
    make_og(out / "og.png", "zh")
    make_og(out / "en" / "og.png", "en")
    print("generated:", out / "index.html")
    print("generated:", out / "en" / "index.html")
    print("numbers (both languages, asserted equal):", numbers["zh"])
    if pending:
        print("pending translations (译文待同步):")
        for p in pending:
            print("  -", p)
    else:
        print("pending translations (译文待同步): 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

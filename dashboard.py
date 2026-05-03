"""
prompt-ai dashboard
Terminal viewer for the scraped viral video JSON data.

Usage:
  python dashboard.py              # show all
  python dashboard.py tiktok       # filter by platform
  python dashboard.py youtube
  python dashboard.py instagram
  python dashboard.py twitter
"""

import json
import sys
from pathlib import Path

# ── Path config (mirrors scraper.py logic) ────────────────────────────────────
_THIS_FILE = Path(__file__).resolve()
if _THIS_FILE.parent.name == "src":
    PROJECT_ROOT = _THIS_FILE.parent.parent   # prompt-ai/src/dashboard.py
else:
    PROJECT_ROOT = _THIS_FILE.parent          # prompt-ai/dashboard.py

DATA_DIR  = PROJECT_ROOT / "data"
JSON_FILE = DATA_DIR / "viral_ai_videos.json"


# ── Load ──────────────────────────────────────────────────────────────────────

def load_records():
    if not JSON_FILE.exists():
        print(f"No data file found at: {JSON_FILE}")
        print("Run scraper.py first to collect data.")
        sys.exit(1)
    try:
        content = JSON_FILE.read_text(encoding="utf-8").strip()
        if not content:
            print("Data file is empty. Run scraper.py first.")
            sys.exit(1)
        return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Corrupted JSON file: {e}")
        print(f"File: {JSON_FILE}")
        print("Fix: delete the file and run scraper.py again to rebuild it.")
        sys.exit(1)


# ── Display ───────────────────────────────────────────────────────────────────

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def print_video(i, v):
    print(color(f"\n{'─'*70}", "90"))
    print(color(f"[{i}] {v.get('title', 'Untitled')}", "1;97"))

    print(
        f"  {color('Platform:', '90')} {v.get('platform', 'Unknown')}   "
        f"{color('Tool:', '90')} {v.get('ai_tool', 'Unknown')}   "
        f"{color('Creator:', '90')} {v.get('creator', 'Unknown')}   "
        f"{color('Found:', '90')} {v.get('date_found', '?')}"
    )

    url = v.get("url")
    if url:
        print(f"  {color('URL:', '90')} {color(url, '36')}")

    desc = v.get("description", "")
    if desc:
        print(f"\n  {color('Description:', '33')} {desc[:300]}{'...' if len(desc) > 300 else ''}")

    prompt = v.get("prompt", {})
    if prompt.get("available"):
        print(f"\n  {color('PROMPT FOUND', '32')} (source: {prompt.get('source', '?')})")
        text = prompt.get("text") or ""
        if text:
            display = text[:400] + ("..." if len(text) > 400 else "")
            print(f"\n  {color('Prompt:', '92')}\n  {display}")
    else:
        print(f"\n  {color('Prompt not available', '91')} (source: {prompt.get('source', '?')})")

    steps = prompt.get("steps", [])
    if steps:
        print(f"\n  {color('Steps:', '93')}")
        for step in steps:
            print(f"    - {step}")

    tags = v.get("tags", [])
    if tags:
        print(f"\n  {color('Tags:', '90')} {', '.join(tags)}")

def print_summary(records, filtered, platform_filter):
    platforms, tools = {}, {}
    with_prompt = sum(1 for r in records if r.get("prompt", {}).get("available"))

    for r in records:
        p = r.get("platform", "Unknown")
        t = r.get("ai_tool", "Unknown")
        platforms[p] = platforms.get(p, 0) + 1
        tools[t] = tools.get(t, 0) + 1

    print(f"\n{'='*50}")
    print("  prompt-ai  -  Viewer")
    print(f"{'='*50}")
    print(f"\n  File         : {JSON_FILE}")
    print(f"  Total videos : {len(records)}")
    print(f"  With prompts : {with_prompt} / {len(records)}")

    if platform_filter:
        print(f"  Filter       : '{platform_filter}' -> {len(filtered)} results")

    print(f"\n  By platform:")
    for p, c in sorted(platforms.items(), key=lambda x: -x[1]):
        print(f"    {p:<25} {c}")

    print(f"\n  By AI tool:")
    for t, c in sorted(tools.items(), key=lambda x: -x[1])[:10]:
        print(f"    {t:<25} {c}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    records = load_records()
    platform_filter = sys.argv[1].lower() if len(sys.argv) > 1 else None

    filtered = [
        r for r in records
        if not platform_filter or platform_filter in r.get("platform", "").lower()
    ]

    print_summary(records, filtered, platform_filter)

    if not filtered:
        print(f"\n  No results for filter '{platform_filter}'.")
        print("  Try: tiktok, youtube, instagram, twitter\n")
        sys.exit(0)

    for i, v in enumerate(filtered, 1):
        print_video(i, v)

    print(color(f"\n{'─'*70}\n", "90"))

if __name__ == "__main__":
    main()

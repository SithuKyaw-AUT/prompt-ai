"""
prompt-ai dashboard
Quick terminal viewer for the scraped viral video JSON data.
"""

import json
import sys
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_today() -> list[dict]:
    today = datetime.date.today().isoformat()
    path = DATA_DIR / f"viral_ai_videos_{today}.json"
    if not path.exists():
        # Fall back to the most recent file
        files = sorted(DATA_DIR.glob("viral_ai_videos_*.json"), reverse=True)
        if not files:
            print("No data files found. Run scraper.py first.")
            sys.exit(1)
        path = files[0]
        print(f"Using most recent file: {path.name}\n")
    with open(path) as f:
        return json.load(f)


def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def print_video(i: int, v: dict):
    print(color(f"\n{'─'*70}", "90"))
    print(color(f"[{i}] {v.get('title', 'Untitled')}", "1;97"))

    platform = v.get("platform", "Unknown")
    tool = v.get("ai_tool", "Unknown")
    creator = v.get("creator", "Unknown")
    views = v.get("estimated_views", "Unknown")

    print(f"  {color('Platform:', '90')} {platform}   "
          f"{color('Tool:', '90')} {tool}   "
          f"{color('Creator:', '90')} {creator}   "
          f"{color('Views:', '90')} {views}")

    url = v.get("url")
    if url:
        print(f"  {color('URL:', '90')} {color(url, '36')}")

    desc = v.get("description", "")
    if desc:
        print(f"\n  {color('Description:', '33')} {desc}")

    prompt = v.get("prompt", {})
    if prompt.get("available"):
        print(f"\n  {color('✓ PROMPT FOUND', '32')} "
              f"(source: {prompt.get('source', '?')})")
        text = prompt.get("text") or ""
        if text:
            # Truncate for display
            display = text[:400] + ("…" if len(text) > 400 else "")
            print(f"\n  {color('Prompt:', '92')}\n  {display}")
    else:
        print(f"\n  {color('✗ Prompt not available', '91')} "
              f"(source: {prompt.get('source', '?')})")

    steps = prompt.get("steps", [])
    if steps:
        print(f"\n  {color('Steps:', '93')}")
        for step in steps:
            print(f"    • {step}")

    tags = v.get("tags", [])
    if tags:
        print(f"\n  {color('Tags:', '90')} {', '.join(tags)}")


def summary(records: list[dict]):
    platforms = {}
    tools = {}
    with_prompt = sum(1 for r in records if r.get("prompt", {}).get("available"))

    for r in records:
        p = r.get("platform", "Unknown")
        t = r.get("ai_tool", "Unknown")
        platforms[p] = platforms.get(p, 0) + 1
        tools[t] = tools.get(t, 0) + 1

    print(color("\n╔══════════════════════════════════════╗", "36"))
    print(color("║       prompt-ai  •  Daily Report     ║", "36"))
    print(color("╚══════════════════════════════════════╝", "36"))
    print(f"\n  Total videos : {color(len(records), '1;97')}")
    print(f"  With prompts : {color(with_prompt, '32')} / {len(records)}")

    print(f"\n  {color('By platform:', '33')}")
    for p, c in sorted(platforms.items(), key=lambda x: -x[1]):
        print(f"    {p:<25} {c}")

    print(f"\n  {color('By AI tool:', '33')}")
    for t, c in sorted(tools.items(), key=lambda x: -x[1])[:10]:
        print(f"    {t:<25} {c}")


def main():
    records = load_today()
    summary(records)

    # Optional: filter by platform via CLI arg
    platform_filter = sys.argv[1].lower() if len(sys.argv) > 1 else None
    filtered = [
        r for r in records
        if not platform_filter or platform_filter in r.get("platform", "").lower()
    ]

    for i, v in enumerate(filtered, 1):
        print_video(i, v)

    print(color(f"\n{'─'*70}\n", "90"))


if __name__ == "__main__":
    main()

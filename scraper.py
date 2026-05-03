"""
prompt-ai scraper (FREE version)
Finds viral AI-generated short videos and their prompts
using DuckDuckGo search — no API key required.

Run this on YOUR OWN MACHINE (not a restricted server).
Results accumulate in a single file: prompt-ai/data/viral_ai_videos.json
"""

import json
import datetime
import time
import re
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    from ddgs import DDGS
except ImportError:
    raise SystemExit(
        "Missing dependency. Run:  pip install ddgs\n"
        "Then re-run:              python src/scraper.py"
    )

# ── Path config ───────────────────────────────────────────────────────────────
#
# Works no matter how you run the script:
#   python src/scraper.py        (from prompt-ai/)
#   python scraper.py            (from prompt-ai/src/)
#   python prompt-ai/src/scraper.py  (from anywhere)
#
# scraper.py is in either prompt-ai/ or prompt-ai/src/.
# data/ must always be inside prompt-ai/.
#
_THIS_FILE = Path(__file__).resolve()

# If this file is inside a "src" folder, go up two levels; otherwise one.
if _THIS_FILE.parent.name == "src":
    PROJECT_ROOT = _THIS_FILE.parent.parent   # prompt-ai/src/scraper.py → prompt-ai/
else:
    PROJECT_ROOT = _THIS_FILE.parent          # prompt-ai/scraper.py     → prompt-ai/

DATA_DIR  = PROJECT_ROOT / "data"             # prompt-ai/data/
JSON_FILE = DATA_DIR / "viral_ai_videos.json" # single persistent file

def init():
    """Create prompt-ai/data/ and the JSON file if they don't exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not JSON_FILE.exists():
        JSON_FILE.write_text("[]", encoding="utf-8")
        print(f"  Created {JSON_FILE}")

init()

# ── Search queries ────────────────────────────────────────────────────────────

SEARCH_QUERIES = {
    "TikTok": [
        "tiktok viral AI generated video prompt tutorial sora runway kling 2025",
        'tiktok "AI generated" viral video step by step prompt',
        "tiktok viral AI video how to recreate full prompt 2025",
    ],
    "YouTube Shorts": [
        "youtube shorts viral AI generated video prompt breakdown 2025",
        "youtube shorts AI video prompt sora runway pika tutorial",
        '"youtube shorts" AI generated viral video prompt step by step',
    ],
    "Instagram Reels": [
        "instagram reels AI generated viral video prompt tutorial 2025",
        'instagram "AI generated" viral reel step by step prompt',
        "instagram AI video viral prompt breakdown sora runway kling 2025",
    ],
    "X (Twitter)": [
        "twitter viral AI generated video prompt sora runway kling pika 2025",
        'site:x.com "AI generated" viral video prompt breakdown',
        "x.com viral AI video prompt tutorial step by step 2025",
    ],
}

PROMPT_QUERIES = [
    "viral AI video exact prompt breakdown step by step 2025",
    "AI generated viral short film prompt tutorial sora runway gen3",
    "how to recreate viral AI video full prompt midjourney sora kling",
    "AI video prompt that went viral tiktok youtube instagram 2025",
    "AI short video prompt reddit midjourney sora kling tutorial 2025",
]

AI_TOOLS = [
    "Sora", "Runway", "Gen-3", "Gen-2", "Kling", "Pika", "Midjourney",
    "Stable Diffusion", "DALL-E", "Luma", "Dream Machine", "Veo",
    "Hailuo", "MiniMax", "CogVideoX", "AnimateDiff", "Wan", "Mochi",
]

PLATFORM_DOMAINS = {
    "TikTok":           ["tiktok.com"],
    "YouTube Shorts":   ["youtube.com/shorts", "youtu.be"],
    "Instagram Reels":  ["instagram.com"],
    "X (Twitter)":      ["twitter.com", "x.com"],
}


# ── File I/O ──────────────────────────────────────────────────────────────────

def load_existing():
    """Load all records from the single JSON file, handling corruption safely."""
    try:
        content = JSON_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  WARNING: Corrupted JSON ({e}), resetting file to []")
        JSON_FILE.write_text("[]", encoding="utf-8")
        return []

def save(records):
    """Write all records back to the single JSON file."""
    JSON_FILE.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  Saved {len(records)} total records -> {JSON_FILE}")


# ── Deduplication ─────────────────────────────────────────────────────────────

def make_fingerprint(record):
    """
    Stable unique key per record so we never add the same video twice,
    even across multiple runs on different days.
    Priority: URL (stripped of query params) -> normalised title.
    """
    url = record.get("url", "").split("?")[0].strip().rstrip("/").lower()
    if url:
        return f"url:{url}"
    title = re.sub(r"\s+", " ", record.get("title", "")).strip().lower()
    return f"title:{title}"

def deduplicate(records):
    """Remove duplicates keeping the first occurrence of each fingerprint."""
    seen = set()
    unique = []
    for r in records:
        fp = make_fingerprint(r)
        if not fp or fp in seen:
            continue
        seen.add(fp)
        unique.append(r)
    return unique


# ── Helpers ───────────────────────────────────────────────────────────────────

def today():
    return datetime.date.today().isoformat()

def detect_platform(url):
    for platform, domains in PLATFORM_DOMAINS.items():
        for domain in domains:
            if domain in url:
                return platform
    return "Unknown"

def detect_ai_tool(text):
    text_lower = text.lower()
    for tool in AI_TOOLS:
        if tool.lower() in text_lower:
            return tool
    return "Unknown"

def extract_prompt_hints(text):
    prompt_patterns = [
        r'prompt[:\s"\']+([^.!?\n]{20,300})',
        r'"([^"]{30,300})"',
        r'step\s*\d+[:\s]+([^.!?\n]{20,200})',
    ]
    found = []
    for pattern in prompt_patterns:
        found.extend(re.findall(pattern, text, re.IGNORECASE))

    has_keywords = any(
        kw in text.lower()
        for kw in ["prompt", "step by step", "tutorial", "how to", "recreate", "settings"]
    )

    if found:
        return {
            "available": True,
            "text": found[0].strip(),
            "source": "search snippet",
            "steps": [s.strip() for s in found[:5] if len(s.strip()) > 15],
        }
    if has_keywords:
        return {
            "available": False,
            "text": None,
            "source": "reconstructed",
            "steps": [
                "Step 1: Visit the original post URL to find the full prompt",
                "Step 2: Check the video description and pinned comments",
                "Step 3: Search for the creator's follow-up posts about their workflow",
            ],
        }
    return {"available": False, "text": None, "source": "unavailable", "steps": []}

def extract_tags(text):
    tags = set()
    for tool in AI_TOOLS:
        if tool.lower() in text.lower():
            tags.add(tool.lower())
    for kw in ["viral", "cinematic", "realistic", "animation", "tutorial",
               "trending", "ai art", "generated", "timelapse", "slow motion"]:
        if kw in text.lower():
            tags.add(kw)
    return list(tags)[:8]

def is_ai_video_result(title, snippet):
    text = (title + " " + snippet).lower()
    ai_terms = [
        "ai generated", "ai video", "ai art", "sora", "runway", "kling",
        "pika", "midjourney", "stable diffusion", "ai created", "generated with ai",
        "ai short", "text to video", "ai film", "luma dream", "veo",
    ]
    return any(term in text for term in ai_terms)

def ddg_search(query, max_results=8):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
    except Exception as e:
        print(f"    Search error: {e}")
        return []


# ── Core scraper ──────────────────────────────────────────────────────────────

def build_record(title, url, snippet, fallback_platform):
    platform = detect_platform(url)
    if platform == "Unknown":
        platform = fallback_platform
    return {
        "title":           title,
        "platform":        platform,
        "creator":         "Unknown",
        "url":             url,
        "ai_tool":         detect_ai_tool(title + " " + snippet),
        "description":     snippet,
        "prompt":          extract_prompt_hints(snippet),
        "tags":            extract_tags(title + " " + snippet),
        "estimated_views": "Unknown",
        "date_found":      today(),
    }

def scrape_platform(platform, queries):
    records = []
    for query in queries:
        print(f"  Searching: {query[:72]}...")
        for r in ddg_search(query):
            title   = r["title"].strip()
            url     = r["url"].strip()
            snippet = r["snippet"].strip()
            if not title or not url:
                continue
            if not is_ai_video_result(title, snippet):
                continue
            records.append(build_record(title, url, snippet, platform))
        time.sleep(1.0)
    return records

def scrape_prompt_focused():
    records = []
    print("\nPrompt-focused pass...")
    for query in PROMPT_QUERIES:
        print(f"  Searching: {query[:72]}...")
        for r in ddg_search(query, max_results=10):
            title   = r["title"].strip()
            url     = r["url"].strip()
            snippet = r["snippet"].strip()
            if not title or not url:
                continue
            platform    = detect_platform(url) or "Web / Blog"
            prompt_data = extract_prompt_hints(snippet)
            if not prompt_data["available"] and platform == "Web / Blog":
                continue
            records.append({
                "title":           title,
                "platform":        platform,
                "creator":         "Unknown",
                "url":             url,
                "ai_tool":         detect_ai_tool(title + " " + snippet),
                "description":     snippet,
                "prompt":          prompt_data,
                "tags":            extract_tags(title + " " + snippet),
                "estimated_views": "Unknown",
                "date_found":      today(),
            })
        time.sleep(1.0)
    return records


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("\n=============================================")
    print("  prompt-ai  -  Free Scraper (No API Key)")
    print("=============================================")
    print(f"\n  Project root : {PROJECT_ROOT}")
    print(f"  Data file    : {JSON_FILE}\n")

    # Load everything already in the file (all previous runs)
    all_records = load_existing()
    before = len(all_records)
    print(f"  Existing records : {before}\n")

    new_records = []

    for platform, queries in SEARCH_QUERIES.items():
        print(f"\n[ {platform} ]")
        new_records.extend(scrape_platform(platform, queries))

    new_records.extend(scrape_prompt_focused())

    # Merge existing + new, deduplicate the whole lot
    all_records = deduplicate(all_records + new_records)
    added = len(all_records) - before

    save(all_records)

    with_prompts = sum(1 for r in all_records if r["prompt"]["available"])
    print(f"\nDone!")
    print(f"  New records added : {added}")
    print(f"  Total records     : {len(all_records)}")
    print(f"  With prompts      : {with_prompts}")
    print(f"  File              : {JSON_FILE}\n")

if __name__ == "__main__":
    run()

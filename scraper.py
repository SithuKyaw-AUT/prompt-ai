"""
prompt-ai scraper (FREE version)
Finds viral AI-generated short videos and their prompts
using DuckDuckGo search — no API key required.

Run this on YOUR OWN MACHINE (not a restricted server).
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

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"

def init_data_dir():
    """Create data/ folder and today's empty JSON file if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"viral_ai_videos_{datetime.date.today().isoformat()}.json"
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
        print(f"  Created {path}")

init_data_dir()

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
    "TikTok": ["tiktok.com"],
    "YouTube Shorts": ["youtube.com/shorts", "youtu.be"],
    "Instagram Reels": ["instagram.com"],
    "X (Twitter)": ["twitter.com", "x.com"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def today():
    return datetime.date.today().isoformat()

def output_path():
    return DATA_DIR / f"viral_ai_videos_{today()}.json"

def load_existing():
    path = output_path()
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠ Corrupted JSON detected ({e}), resetting file to []")
        path.write_text("[]", encoding="utf-8")
        return []

def save(records):
    path = output_path()
    with open(path, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(records)} records → {path}")

def deduplicate(records):
    seen_urls, seen_titles = set(), set()
    unique = []
    for r in records:
        url = r.get("url", "").split("?")[0]
        title = r.get("title", "").lower().strip()
        if not title or title in seen_titles:
            continue
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        seen_titles.add(title)
        unique.append(r)
    return unique

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
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)

    has_prompt_keywords = any(
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
    elif has_prompt_keywords:
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
    tags = []
    for tool in AI_TOOLS:
        if tool.lower() in text.lower():
            tags.append(tool.lower())
    for kw in ["viral", "cinematic", "realistic", "animation", "tutorial",
               "trending", "ai art", "generated", "timelapse", "slow motion"]:
        if kw in text.lower():
            tags.append(kw)
    return list(set(tags))[:8]

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
                    "title": r.get("title", ""),
                    "url":   r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
    except Exception as e:
        print(f"    ⚠ Search error: {e}")
        return []


# ── Core scraper ──────────────────────────────────────────────────────────────

def build_record(title, url, snippet, fallback_platform):
    platform = detect_platform(url)
    if platform == "Unknown":
        platform = fallback_platform
    return {
        "title": title,
        "platform": platform,
        "creator": "Unknown",
        "url": url,
        "ai_tool": detect_ai_tool(title + " " + snippet),
        "description": snippet,
        "prompt": extract_prompt_hints(snippet),
        "tags": extract_tags(title + " " + snippet),
        "estimated_views": "Unknown",
        "date_found": today(),
    }

def scrape_platform(platform, queries):
    records = []
    for query in queries:
        print(f"  🔍 {query[:70]}...")
        results = ddg_search(query)
        for r in results:
            title = r["title"].strip()
            url = r["url"].strip()
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
    print("\n🎯 Prompt-focused pass...")
    for query in PROMPT_QUERIES:
        print(f"  🔍 {query[:70]}...")
        results = ddg_search(query, max_results=10)
        for r in results:
            title = r["title"].strip()
            url = r["url"].strip()
            snippet = r["snippet"].strip()
            if not title or not url:
                continue
            platform = detect_platform(url)
            if platform == "Unknown":
                platform = "Web / Blog"
            prompt_data = extract_prompt_hints(snippet)
            # For generic web results, only keep if there's prompt content
            if not prompt_data["available"] and platform == "Web / Blog":
                continue
            records.append({
                "title": title,
                "platform": platform,
                "creator": "Unknown",
                "url": url,
                "ai_tool": detect_ai_tool(title + " " + snippet),
                "description": snippet,
                "prompt": prompt_data,
                "tags": extract_tags(title + " " + snippet),
                "estimated_views": "Unknown",
                "date_found": today(),
            })
        time.sleep(1.0)
    return records


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("\n╔══════════════════════════════════════════╗")
    print("║  prompt-ai  •  Free Scraper (No API Key) ║")
    print("╚══════════════════════════════════════════╝\n")

    all_records = load_existing()
    print(f"Loaded {len(all_records)} existing records for today.\n")

    for platform, queries in SEARCH_QUERIES.items():
        print(f"\n📱 {platform}")
        new = scrape_platform(platform, queries)
        all_records.extend(new)
        all_records = deduplicate(all_records)
        save(all_records)

    prompt_records = scrape_prompt_focused()
    all_records.extend(prompt_records)
    all_records = deduplicate(all_records)
    save(all_records)

    with_prompts = sum(1 for r in all_records if r["prompt"]["available"])
    print(f"\n✅ Done!")
    print(f"   Total videos : {len(all_records)}")
    print(f"   With prompts : {with_prompts}")
    print(f"   Output       : {output_path()}\n")

if __name__ == "__main__":
    run()

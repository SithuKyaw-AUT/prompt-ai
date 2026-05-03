"""
prompt-ai scraper
Finds daily viral AI-generated short videos and their prompts
across TikTok, YouTube Shorts, Instagram Reels, and X (Twitter).
"""

import os
import json
import datetime
import time
import re
import anthropic
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PLATFORMS = ["TikTok", "YouTube Shorts", "Instagram Reels", "X (Twitter)"]

SEARCH_QUERIES = [
    "viral AI generated short video TikTok 2025 prompt",
    "viral AI video YouTube Shorts trending AI generated 2025",
    "Instagram Reels AI generated viral video prompts 2025",
    "X Twitter viral AI generated video prompt tutorial 2025",
    "trending AI video Sora Runway Kling Pika prompt tutorial",
    "viral AI short film prompt breakdown step by step",
    "midjourney sora runway gen3 viral video prompt 2025",
    "AI generated viral video how to recreate prompt",
]

SYSTEM_PROMPT = """You are an expert researcher specialising in viral AI-generated video content.
Your job is to identify real, currently trending or recently viral AI-generated short videos 
across social media platforms and extract or reconstruct their step-by-step prompts.

For each video you identify, return a JSON array of objects with this EXACT schema:

[
  {
    "title": "Short descriptive title of the video",
    "platform": "TikTok | YouTube Shorts | Instagram Reels | X (Twitter)",
    "creator": "Creator username or handle (or 'Unknown')",
    "url": "Direct URL to the video or post (or best guess / search URL)",
    "ai_tool": "Tool used e.g. Sora, Runway Gen-3, Kling, Pika, Midjourney, Stable Diffusion, etc.",
    "description": "What happens in the video (2-3 sentences)",
    "prompt": {
      "available": true or false,
      "text": "The full prompt text if available, otherwise null",
      "source": "Where the prompt was found: 'video description', 'comment', 'creator post', 'reconstructed', 'unavailable'",
      "steps": [
        "Step 1: ...",
        "Step 2: ...",
        "Step N: ..."
      ]
    },
    "tags": ["tag1", "tag2"],
    "estimated_views": "e.g. '2.3M' or 'Unknown'",
    "date_found": "YYYY-MM-DD"
  }
]

Rules:
- Only include AI-generated videos (not videos ABOUT AI tools).
- Include as many real examples as you can find (aim for 5-10 per search).
- If the exact prompt is unavailable, set available=false and reconstruct a plausible step-by-step 
  breakdown in 'steps' based on the video content and the AI tool used.
- Return ONLY valid JSON — no markdown, no preamble, no trailing text.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def today() -> str:
    return datetime.date.today().isoformat()


def output_path() -> Path:
    return DATA_DIR / f"viral_ai_videos_{today()}.json"


def load_existing() -> list[dict]:
    path = output_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save(records: list[dict]) -> None:
    path = output_path()
    with open(path, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(records)} records → {path}")


def deduplicate(records: list[dict]) -> list[dict]:
    seen_urls, seen_titles = set(), set()
    unique = []
    for r in records:
        url = r.get("url", "")
        title = r.get("title", "").lower().strip()
        if url in seen_urls or title in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title)
        unique.append(r)
    return unique


def parse_json_response(text: str) -> list[dict]:
    """Extract JSON array from model response, tolerating markdown fences."""
    text = text.strip()
    # strip ```json ... ``` fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON parse error: {e}")
    return []


# ── Core search ───────────────────────────────────────────────────────────────

def search_viral_videos(client: anthropic.Anthropic, query: str) -> list[dict]:
    """Run one web-search-enabled Claude call and return parsed records."""
    print(f"  🔍 Query: {query}")
    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Search the web for: {query}\n\n"
                        f"Today's date: {today()}\n\n"
                        "Find viral AI-generated short videos and their prompts. "
                        "Return a JSON array following the schema in your instructions."
                    ),
                }
            ],
        )

        # Collect all text blocks from the response
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        records = parse_json_response(full_text)
        # Stamp date_found if missing
        for r in records:
            r.setdefault("date_found", today())
        print(f"    → Found {len(records)} videos")
        return records

    except anthropic.APIError as e:
        print(f"  ✗ API error: {e}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("\n╔══════════════════════════════════════╗")
    print("║   prompt-ai  •  Daily Video Scraper  ║")
    print("╚══════════════════════════════════════╝\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Export it before running:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)

    all_records = load_existing()
    print(f"Loaded {len(all_records)} existing records for today.\n")

    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"[{i}/{len(SEARCH_QUERIES)}] Searching...")
        new_records = search_viral_videos(client, query)
        all_records.extend(new_records)

        # Deduplicate and save after every query
        all_records = deduplicate(all_records)
        save(all_records)

        # Be polite to the API
        if i < len(SEARCH_QUERIES):
            time.sleep(2)

    print(f"\n✅ Done! {len(all_records)} unique viral AI videos saved.")
    print(f"   Output → {output_path()}\n")


if __name__ == "__main__":
    run()

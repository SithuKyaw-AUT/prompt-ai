# prompt-ai 🎬

> Daily scraper for viral AI-generated short videos and their step-by-step prompts.  
> **100% free — no API key required.**

Covers **TikTok**, **YouTube Shorts**, **Instagram Reels**, and **X (Twitter)**.  
Uses DuckDuckGo search to find trending AI videos and extract their prompts.

---

## Setup (run on your own machine)

```bash
# 1. Clone
git clone https://github.com/SithuKyaw-AUT/prompt-ai.git
cd prompt-ai

# 2. Install (only one dependency!)
pip install ddgs

# 3. Run
python src/scraper.py
```

That's it. No API key. No account. No cost.

---

## Usage

### Run the scraper
```bash
python src/scraper.py
```
Results are saved to `data/viral_ai_videos_YYYY-MM-DD.json`.

### View results in terminal
```bash
# All platforms
python src/dashboard.py

# Filter by platform
python src/dashboard.py tiktok
python src/dashboard.py youtube
python src/dashboard.py instagram
python src/dashboard.py twitter
```

---

## Output format (JSON)

```json
{
  "title": "Hyper-realistic underwater city flythrough",
  "platform": "YouTube Shorts",
  "creator": "Unknown",
  "url": "https://youtube.com/shorts/...",
  "ai_tool": "Sora",
  "description": "A sweeping aerial shot through a glowing underwater metropolis...",
  "prompt": {
    "available": true,
    "text": "Cinematic drone shot flying through an underwater city...",
    "source": "search snippet",
    "steps": [
      "Step 1: Set the scene — underwater metropolis, bioluminescent lighting",
      "Step 2: Camera movement — slow drone pullback revealing the full city",
      "Step 3: Style — photorealistic, 8K, cinematic colour grading"
    ]
  },
  "tags": ["sora", "cinematic", "viral", "ai generated"],
  "estimated_views": "Unknown",
  "date_found": "2026-05-03"
}
```

---

## Automate daily runs

```bash
# Mac/Linux — add to crontab (runs every day at 9am)
crontab -e
# Add this line:
0 9 * * * cd /path/to/prompt-ai && python src/scraper.py
```

---

## Project structure

```
prompt-ai/
├── src/
│   ├── scraper.py       # Main scraper (DuckDuckGo, free)
│   └── dashboard.py     # Terminal viewer
├── data/
│   └── viral_ai_videos_YYYY-MM-DD.json
├── requirements.txt     # Just: ddgs
└── README.md
```

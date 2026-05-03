# prompt-ai 🎬

> Daily scraper for viral AI-generated short videos and their step-by-step prompts.

Covers **TikTok**, **YouTube Shorts**, **Instagram Reels**, and **X (Twitter)**.  
Uses Claude + web search to find trending videos and extract (or reconstruct) their prompts.

---

## Setup

```bash
# 1. Clone
git clone https://github.com/SithuKyaw-AUT/prompt-ai.git
cd prompt-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Run the scraper
```bash
python src/scraper.py
```

Results are saved to `data/viral_ai_videos_YYYY-MM-DD.json`.

### View the dashboard
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

## Output Format

Each record in the JSON file follows this schema:

```json
{
  "title": "Hyper-realistic underwater city flythrough",
  "platform": "YouTube Shorts",
  "creator": "@ai_visuals",
  "url": "https://youtube.com/shorts/...",
  "ai_tool": "Sora",
  "description": "A sweeping aerial shot through a glowing underwater metropolis...",
  "prompt": {
    "available": true,
    "text": "Cinematic drone shot flying through an underwater city...",
    "source": "video description",
    "steps": [
      "Step 1: Set the scene — underwater metropolis, bioluminescent lighting",
      "Step 2: Camera movement — slow drone pullback revealing the full city",
      "Step 3: Style — photorealistic, 8K, cinematic colour grading"
    ]
  },
  "tags": ["underwater", "cinematic", "sora", "viral"],
  "estimated_views": "4.2M",
  "date_found": "2025-05-03"
}
```

### Prompt availability

| `prompt.available` | `prompt.source`      | Meaning                                      |
|--------------------|----------------------|----------------------------------------------|
| `true`             | `video description`  | Prompt found in the video's description      |
| `true`             | `comment`            | Creator shared the prompt in comments        |
| `true`             | `creator post`       | Prompt shared in a follow-up post            |
| `false`            | `reconstructed`      | Prompt not public; steps are best-effort     |
| `false`            | `unavailable`        | No prompt information found                  |

---

## Automate daily runs

Add to crontab to run every day at 9 AM:

```bash
crontab -e
# Add:
0 9 * * * cd /path/to/prompt-ai && ANTHROPIC_API_KEY=sk-ant-... python src/scraper.py
```

---

## Project structure

```
prompt-ai/
├── src/
│   ├── scraper.py       # Main scraper (Claude + web search)
│   └── dashboard.py     # Terminal viewer
├── data/
│   └── viral_ai_videos_YYYY-MM-DD.json
├── requirements.txt
└── README.md
```

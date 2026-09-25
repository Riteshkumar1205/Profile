import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("generate_dashboard")

REPO_ROOT = Path(__file__).parent.parent
README_FILE = REPO_ROOT / "README.md"
ACTIVITY_FILE = REPO_ROOT / "data" / "activity.json"

DYNAMIC_START = "<!-- DYNAMIC-RECENT:START -->"
DYNAMIC_END = "<!-- DYNAMIC-RECENT:END -->"
API_BASE = "https://api.github.com"
USERNAME = os.environ.get("GITHUB_USERNAME", "Riteshkumar1205")

def make_request(url: str, token: str | None = None) -> list:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ProfileMetricsBot/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def generate_recently_updated() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    try:
        url = f"{API_BASE}/users/{USERNAME}/repos?sort=updated&per_page=15"
        repos = make_request(url, token)
        
        # Filter out forks and the profile repository itself
        original_repos = [r for r in repos if not r.get("fork") and r.get("name") != USERNAME]
        
        # Take top 4 most recently updated
        recent = original_repos[:4]
        
        if not recent:
            return "*No recent activity found.*"
            
        lines = []
        for repo in recent:
            name = repo.get("name", "Unknown")
            url = repo.get("html_url", "#")
            pushed_at = repo.get("pushed_at", "")
            
            # Format date beautifully
            date_str = ""
            if pushed_at:
                dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%B %d, %Y")
                
            lines.append(f"- **[{name}]({url})** — *Updated: {date_str}*")
            
        # Save to activity.json
        ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
            json.dump(recent, f, indent=2, ensure_ascii=False)
            
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Failed to fetch recent activity: {e}")
        return "*Failed to fetch recent activity.*"

def inject_into_readme(dynamic_content: str):
    if not README_FILE.exists():
        logger.error("README.md not found.")
        return

    readme = README_FILE.read_text(encoding="utf-8")
    start_idx = readme.find(DYNAMIC_START)
    end_idx = readme.find(DYNAMIC_END)

    if start_idx == -1 or end_idx == -1:
        logger.error("DYNAMIC-RECENT markers not found in README.md")
        return

    start_line_end = readme.index("\n", start_idx) + 1
    new_section = f"{readme[start_idx:start_line_end]}{dynamic_content}\n{DYNAMIC_END}"
    new_readme = readme[:start_idx] + new_section + readme[end_idx + len(DYNAMIC_END):]

    if new_readme != readme:
        README_FILE.write_text(new_readme, encoding="utf-8")
        logger.info("README.md updated with recent activity.")
    else:
        logger.info("README.md unchanged.")

def main():
    logger.info("Generating dashboard/activity section...")
    content = generate_recently_updated()
    inject_into_readme(content)

if __name__ == "__main__":
    main()

"""
GitHub Metrics Fetcher
======================
Fetches public GitHub profile and repository metrics using the GitHub REST API.

Returns: dict with status, public_repos, followers, following, total_stars,
         top_languages, and account_created fields.
"""

import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("fetch_github")

API_BASE = "https://api.github.com"
TIMEOUT = 15  # seconds


def _make_request(url: str, token: str | None = None) -> dict:
    """Make authenticated GitHub API request."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ProfileMetricsBot/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_github_metrics(username: str) -> dict:
    """
    Fetch GitHub metrics for the given username.

    Args:
        username: GitHub username

    Returns:
        dict with status='success' and metrics, or status='error' with error message
    """
    token = os.environ.get("GITHUB_TOKEN")

    try:
        # Fetch user profile
        user = _make_request(f"{API_BASE}/users/{username}", token)

        # Fetch all public repos (paginated)
        repos = []
        page = 1
        while True:
            page_repos = _make_request(
                f"{API_BASE}/users/{username}/repos?per_page=100&page={page}&type=owner",
                token
            )
            if not page_repos:
                break
            repos.extend(page_repos)
            if len(page_repos) < 100:
                break
            page += 1

        # Calculate metrics
        total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
        total_forks = sum(r.get("forks_count", 0) for r in repos if not r.get("fork"))

        # Top languages (from non-fork repos)
        lang_counts = {}
        for r in repos:
            if not r.get("fork") and r.get("language"):
                lang = r["language"]
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        top_languages = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:8]

        return {
            "status": "success",
            "username": username,
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "top_languages": [{"language": lang, "count": count} for lang, count in top_languages],
            "account_created": user.get("created_at", ""),
            "bio": user.get("bio", ""),
            "repos_fetched": len(repos),
            "original_repos": len([r for r in repos if not r.get("fork")])
        }

    except HTTPError as e:
        logger.error(f"GitHub API HTTP error: {e.code} {e.reason}")
        return {"status": "error", "error": f"HTTP {e.code}: {e.reason}"}
    except URLError as e:
        logger.error(f"GitHub API connection error: {e.reason}")
        return {"status": "error", "error": f"Connection error: {e.reason}"}
    except Exception as e:
        logger.error(f"GitHub fetch error: {e}")
        return {"status": "error", "error": str(e)}

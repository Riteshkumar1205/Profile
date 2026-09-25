"""
Hack The Box Metrics Fetcher
==============================
Fetches Hack The Box profile statistics.

Note: HTB's public API has limited availability. This fetcher
implements graceful fallback and supports optional API key auth.

Returns: dict with status, rank, points, and other available fields.
"""

import json
import os
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("fetch_htb")

HTB_API_BASE = "https://www.hackthebox.com/api/v4"
TIMEOUT = 15  # seconds


def fetch_htb_metrics(username: str) -> dict:
    """
    Fetch Hack The Box stats for the given username.

    Uses the public profile API if available, with optional API key auth.

    Args:
        username: HTB username or profile identifier

    Returns:
        dict with status='success' and metrics, or status='error' with error message
    """
    api_key = os.environ.get("HTB_API_KEY")

    headers = {
        "User-Agent": "ProfileMetricsBot/1.0",
        "Accept": "application/json"
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Try public profile endpoints
    endpoints = [
        f"{HTB_API_BASE}/profile/public/{username}",
        f"https://www.hackthebox.com/api/v4/search/fetch?query={username}&tags=[]",
    ]

    for url in endpoints:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if isinstance(data, dict):
                profile = data.get("profile", data.get("data", data))

                if isinstance(profile, dict):
                    rank = profile.get("rank", profile.get("ranking", "—"))
                    points = profile.get("points", 0)
                    user_owns = profile.get("user_owns", 0)
                    system_owns = profile.get("system_owns", 0)
                    country = profile.get("country_name", "")

                    return {
                        "status": "success",
                        "username": username,
                        "rank": rank,
                        "points": points,
                        "user_owns": user_owns,
                        "system_owns": system_owns,
                        "country": country,
                        "source_url": url
                    }

        except HTTPError as e:
            if e.code == 401:
                logger.warning("HTB API requires authentication")
                continue
            elif e.code == 404:
                logger.warning(f"HTB profile not found at {url}")
                continue
            elif e.code == 429:
                logger.warning("HTB rate limited")
                return {"status": "error", "error": "Rate limited"}
            else:
                logger.warning(f"HTB HTTP {e.code} at {url}")
                continue
        except URLError as e:
            logger.warning(f"HTB connection error at {url}: {e.reason}")
            continue
        except Exception as e:
            logger.warning(f"HTB parse error at {url}: {e}")
            continue

    # All endpoints failed — this is expected for HTB without API key
    return {
        "status": "error",
        "error": "HTB public API unavailable or requires authentication. Profile viewable at hackthebox.com",
        "username": username,
        "profile_url": f"https://app.hackthebox.com/profile/{username}"
    }

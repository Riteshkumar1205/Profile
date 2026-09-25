"""
TryHackMe Metrics Fetcher
==========================
Fetches TryHackMe profile statistics from the public API.

Note: TryHackMe's public API availability may vary. This fetcher
implements graceful fallback if the API is unavailable or rate-limited.

Returns: dict with status, rank, rooms_completed, badges, and points fields.
"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("fetch_tryhackme")

THM_API_BASE = "https://tryhackme.com/api/v2"
TIMEOUT = 15  # seconds


def fetch_tryhackme_metrics(username: str) -> dict:
    """
    Fetch TryHackMe stats for the given username.

    Attempts multiple API endpoints with fallback.

    Args:
        username: TryHackMe username

    Returns:
        dict with status='success' and metrics, or status='error' with error message
    """
    headers = {
        "User-Agent": "ProfileMetricsBot/1.0",
        "Accept": "application/json"
    }

    # Try the public user endpoint
    endpoints = [
        f"{THM_API_BASE}/users/{username}",
        f"https://tryhackme.com/api/user/rank/{username}",
    ]

    for url in endpoints:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Parse response based on structure
            if isinstance(data, dict):
                # Check for nested user data
                user_data = data.get("data", data)

                rank = (
                    user_data.get("rank") or
                    user_data.get("userRank") or
                    "—"
                )
                rooms = (
                    user_data.get("roomsCompleted") or
                    user_data.get("totalRoomsCompleted") or
                    0
                )
                badges = (
                    user_data.get("badges") or
                    user_data.get("totalBadges") or
                    0
                )
                points = (
                    user_data.get("points") or
                    user_data.get("totalPoints") or
                    0
                )
                level = user_data.get("level", "—")

                return {
                    "status": "success",
                    "username": username,
                    "rank": rank,
                    "rooms_completed": rooms,
                    "badges": badges if isinstance(badges, int) else len(badges) if isinstance(badges, list) else 0,
                    "points": points,
                    "level": level,
                    "source_url": url
                }

        except HTTPError as e:
            if e.code == 404:
                logger.warning(f"TryHackMe user not found at {url}")
                continue
            elif e.code == 429:
                logger.warning("TryHackMe rate limited")
                return {"status": "error", "error": "Rate limited"}
            else:
                logger.warning(f"TryHackMe HTTP {e.code} at {url}")
                continue
        except URLError as e:
            logger.warning(f"TryHackMe connection error at {url}: {e.reason}")
            continue
        except Exception as e:
            logger.warning(f"TryHackMe parse error at {url}: {e}")
            continue

    # All endpoints failed
    return {
        "status": "error",
        "error": "All TryHackMe API endpoints failed or returned unexpected data",
        "username": username
    }

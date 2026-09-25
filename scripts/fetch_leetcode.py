"""
LeetCode Metrics Fetcher
=========================
Fetches LeetCode problem-solving statistics using the public GraphQL API.

Returns: dict with status, total_solved, easy_solved, medium_solved,
         hard_solved, acceptance_rate, and ranking fields.
"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("fetch_leetcode")

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"
TIMEOUT = 15  # seconds


def fetch_leetcode_metrics(username: str) -> dict:
    """
    Fetch LeetCode stats for the given username via GraphQL API.

    Args:
        username: LeetCode username

    Returns:
        dict with status='success' and metrics, or status='error' with error message
    """
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
            }
            submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """

    payload = json.dumps({
        "query": query,
        "variables": {"username": username}
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ProfileMetricsBot/1.0",
        "Referer": "https://leetcode.com"
    }

    try:
        req = Request(LEETCODE_GRAPHQL, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        user = data.get("data", {}).get("matchedUser")
        if not user:
            return {"status": "error", "error": f"User '{username}' not found on LeetCode"}

        # Parse submission stats
        stats = user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
        solved = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
        for s in stats:
            diff = s.get("difficulty", "")
            count = s.get("count", 0)
            if diff in solved:
                solved[diff] = count

        ranking = user.get("profile", {}).get("ranking", 0)

        return {
            "status": "success",
            "username": username,
            "total_solved": solved["All"],
            "easy_solved": solved["Easy"],
            "medium_solved": solved["Medium"],
            "hard_solved": solved["Hard"],
            "ranking": ranking
        }

    except HTTPError as e:
        logger.error(f"LeetCode API HTTP error: {e.code}")
        return {"status": "error", "error": f"HTTP {e.code}"}
    except URLError as e:
        logger.error(f"LeetCode API connection error: {e.reason}")
        return {"status": "error", "error": f"Connection error: {e.reason}"}
    except Exception as e:
        logger.error(f"LeetCode fetch error: {e}")
        return {"status": "error", "error": str(e)}

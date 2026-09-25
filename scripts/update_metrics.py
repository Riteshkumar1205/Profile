"""
Profile Metrics Update Orchestrator
====================================
Coordinates metric fetching from all platforms and updates:
  1. data/profile-metrics.json  — structured metrics store
  2. README.md                  — injects dynamic content between DYNAMIC-METRICS markers

Platforms: GitHub, LeetCode, TryHackMe, Hack The Box

Usage:
  python scripts/update_metrics.py

Environment Variables:
  GITHUB_USERNAME    — GitHub username (required)
  LEETCODE_USERNAME  — LeetCode username (required)
  THM_USERNAME       — TryHackMe username (required)
  HTB_USERNAME       — Hack The Box username (required)
  GITHUB_TOKEN       — GitHub token for API auth (optional, increases rate limit)
  THM_API_KEY        — TryHackMe API key (optional)
  HTB_API_KEY        — Hack The Box API key (optional)
  FORCE_UPDATE       — If 'true', update even on partial failures
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_github import fetch_github_metrics
from fetch_leetcode import fetch_leetcode_metrics
from fetch_tryhackme import fetch_tryhackme_metrics
from fetch_htb import fetch_htb_metrics

# ── Configuration ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("update_metrics")

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
METRICS_FILE = DATA_DIR / "profile-metrics.json"
README_FILE = REPO_ROOT / "README.md"

DYNAMIC_START = "<!-- DYNAMIC-METRICS:START"
DYNAMIC_END = "<!-- DYNAMIC-METRICS:END -->"


# ── Helpers ────────────────────────────────────────────────────

def load_existing_metrics() -> dict:
    """Load existing metrics file, or return empty structure."""
    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing metrics: {e}")
    return {}


def save_metrics(metrics: dict) -> None:
    """Save metrics to JSON file with pretty formatting."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Metrics saved to {METRICS_FILE}")


def generate_dynamic_section(metrics: dict) -> str:
    """Generate the dynamic README content from metrics data."""
    timestamp = metrics.get("last_updated", "Unknown")
    sections = []

    # GitHub summary (if available)
    gh = metrics.get("github", {})
    if gh.get("status") == "success":
        sections.append(
            f"**GitHub:** {gh.get('public_repos', '—')} public repositories · "
            f"{gh.get('followers', '—')} followers · "
            f"{gh.get('total_stars', '—')} total stars"
        )

    # LeetCode summary (if available)
    lc = metrics.get("leetcode", {})
    if lc.get("status") == "success":
        solved = lc.get("total_solved", "—")
        easy = lc.get("easy_solved", "—")
        medium = lc.get("medium_solved", "—")
        hard = lc.get("hard_solved", "—")
        sections.append(
            f"**LeetCode:** {solved} problems solved "
            f"(Easy: {easy} · Medium: {medium} · Hard: {hard})"
        )

    # TryHackMe summary (if available)
    thm = metrics.get("tryhackme", {})
    if thm.get("status") == "success":
        rank = thm.get("rank", "—")
        rooms = thm.get("rooms_completed", "—")
        sections.append(
            f"**TryHackMe:** Rank {rank} · {rooms} rooms completed"
        )

    # Hack The Box summary (if available)
    htb = metrics.get("hackthebox", {})
    if htb.get("status") == "success":
        htb_rank = htb.get("rank", "—")
        points = htb.get("points", "—")
        sections.append(
            f"**Hack The Box:** {htb_rank} · {points} points"
        )

    if not sections:
        return ""

    content = "\n".join(f"> {s}" for s in sections)
    content += f"\n>\n> *Automatically updated · Last refresh: {timestamp}*"
    return content


def inject_into_readme(dynamic_content: str) -> bool:
    """
    Replace content between DYNAMIC-METRICS markers in README.md.
    Returns True if README was modified.
    """
    if not README_FILE.exists():
        logger.warning("README.md not found — skipping injection")
        return False

    readme = README_FILE.read_text(encoding="utf-8")

    start_idx = readme.find(DYNAMIC_START)
    end_idx = readme.find(DYNAMIC_END)

    if start_idx == -1 or end_idx == -1:
        logger.warning("DYNAMIC-METRICS markers not found in README.md")
        return False

    # Find the end of the start marker line
    start_line_end = readme.index("\n", start_idx) + 1

    # Build new content
    if dynamic_content:
        new_section = (
            f"{readme[start_idx:start_line_end]}"
            f"{dynamic_content}\n"
            f"{DYNAMIC_END}"
        )
    else:
        new_section = f"{readme[start_idx:start_line_end]}{DYNAMIC_END}"

    new_readme = readme[:start_idx] + new_section + readme[end_idx + len(DYNAMIC_END):]

    if new_readme != readme:
        README_FILE.write_text(new_readme, encoding="utf-8")
        logger.info("README.md updated with dynamic metrics")
        return True

    logger.info("README.md unchanged — no new dynamic content")
    return False


# ── Main ───────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Starting profile metrics update")
    logger.info("=" * 60)

    # Load environment
    github_user = os.environ.get("GITHUB_USERNAME", "Riteshkumar1205")
    leetcode_user = os.environ.get("LEETCODE_USERNAME", "RiteshKumar2512")
    thm_user = os.environ.get("THM_USERNAME", "RITESH26")
    htb_user = os.environ.get("HTB_USERNAME", "Hackglb2025")
    force = os.environ.get("FORCE_UPDATE", "false").lower() == "true"

    # Load previous metrics for fallback
    existing = load_existing_metrics()
    metrics = {"last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    success_count = 0
    total_platforms = 4

    # ── Fetch GitHub ──
    logger.info("Fetching GitHub metrics...")
    try:
        gh = fetch_github_metrics(github_user)
        metrics["github"] = gh
        if gh.get("status") == "success":
            success_count += 1
            logger.info(f"  ✓ GitHub: {gh.get('public_repos')} repos, {gh.get('total_stars')} stars")
        else:
            logger.warning(f"  ✗ GitHub: {gh.get('error', 'unknown error')}")
            # Preserve previous data
            if "github" in existing:
                metrics["github"] = {**existing["github"], "status": "stale"}
    except Exception as e:
        logger.error(f"  ✗ GitHub fetch failed: {e}")
        if "github" in existing:
            metrics["github"] = {**existing["github"], "status": "stale"}
        else:
            metrics["github"] = {"status": "error", "error": str(e)}

    # ── Fetch LeetCode ──
    logger.info("Fetching LeetCode metrics...")
    try:
        lc = fetch_leetcode_metrics(leetcode_user)
        metrics["leetcode"] = lc
        if lc.get("status") == "success":
            success_count += 1
            logger.info(f"  ✓ LeetCode: {lc.get('total_solved')} solved")
        else:
            logger.warning(f"  ✗ LeetCode: {lc.get('error', 'unknown error')}")
            if "leetcode" in existing:
                metrics["leetcode"] = {**existing["leetcode"], "status": "stale"}
    except Exception as e:
        logger.error(f"  ✗ LeetCode fetch failed: {e}")
        if "leetcode" in existing:
            metrics["leetcode"] = {**existing["leetcode"], "status": "stale"}
        else:
            metrics["leetcode"] = {"status": "error", "error": str(e)}

    # ── Fetch TryHackMe ──
    logger.info("Fetching TryHackMe metrics...")
    try:
        thm = fetch_tryhackme_metrics(thm_user)
        metrics["tryhackme"] = thm
        if thm.get("status") == "success":
            success_count += 1
            logger.info(f"  ✓ TryHackMe: rank {thm.get('rank')}")
        else:
            logger.warning(f"  ✗ TryHackMe: {thm.get('error', 'unknown error')}")
            if "tryhackme" in existing:
                metrics["tryhackme"] = {**existing["tryhackme"], "status": "stale"}
    except Exception as e:
        logger.error(f"  ✗ TryHackMe fetch failed: {e}")
        if "tryhackme" in existing:
            metrics["tryhackme"] = {**existing["tryhackme"], "status": "stale"}
        else:
            metrics["tryhackme"] = {"status": "error", "error": str(e)}

    # ── Fetch Hack The Box ──
    logger.info("Fetching Hack The Box metrics...")
    try:
        htb = fetch_htb_metrics(htb_user)
        metrics["hackthebox"] = htb
        if htb.get("status") == "success":
            success_count += 1
            logger.info(f"  ✓ HTB: {htb.get('rank')}, {htb.get('points')} points")
        else:
            logger.warning(f"  ✗ HTB: {htb.get('error', 'unknown error')}")
            if "hackthebox" in existing:
                metrics["hackthebox"] = {**existing["hackthebox"], "status": "stale"}
    except Exception as e:
        logger.error(f"  ✗ Hack The Box fetch failed: {e}")
        if "hackthebox" in existing:
            metrics["hackthebox"] = {**existing["hackthebox"], "status": "stale"}
        else:
            metrics["hackthebox"] = {"status": "error", "error": str(e)}

    # ── Summary ──
    logger.info("-" * 40)
    logger.info(f"Platforms succeeded: {success_count}/{total_platforms}")

    if success_count == 0 and not force:
        logger.error("All platforms failed. Preserving previous metrics.")
        # Don't overwrite if everything failed
        if existing:
            logger.info("Previous metrics preserved.")
            return
        else:
            logger.warning("No previous metrics exist. Writing error state.")

    # Save metrics
    save_metrics(metrics)

    # Generate and inject dynamic README content
    dynamic = generate_dynamic_section(metrics)
    inject_into_readme(dynamic)

    logger.info("=" * 60)
    logger.info("Profile metrics update complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

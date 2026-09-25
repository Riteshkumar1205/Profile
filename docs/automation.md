# Profile Metrics Automation

## Overview

This repository uses **GitHub Actions** to automatically fetch and display metrics from multiple platforms. The system is designed to be **safe**, **idempotent**, and **failure-tolerant**.

## Architecture

```
.github/workflows/update-profile.yml    ← GitHub Actions workflow (daily + manual)
    │
    ▼
scripts/update_metrics.py               ← Orchestrator (coordinates all fetchers)
    │
    ├── scripts/fetch_github.py         ← GitHub REST API (public, uses GITHUB_TOKEN)
    ├── scripts/fetch_leetcode.py       ← LeetCode GraphQL API (public)
    ├── scripts/fetch_tryhackme.py      ← TryHackMe API (public, with fallback)
    └── scripts/fetch_htb.py            ← Hack The Box API (public + optional auth)
    │
    ▼
data/profile-metrics.json              ← Structured metrics store (committed)
README.md                              ← Dynamic content injected between markers
```

## Schedule

- **Automatic:** Daily at 06:00 UTC (11:30 AM IST)
- **Manual:** Run via GitHub Actions → `workflow_dispatch`

## Content Model

The README uses a **hybrid content model**:

### Human-Maintained Sections
- About / engineering philosophy
- Professional identity
- Project narratives and architecture descriptions
- Experience and certifications
- Career direction

### Auto-Generated Sections
- Content between `<!-- DYNAMIC-METRICS:START -->` and `<!-- DYNAMIC-METRICS:END -->` markers
- `data/profile-metrics.json` (full structured data)
- GitHub stats widgets (via github-readme-stats)
- LeetCode card (via leetcard)

> **Rule:** The automation script **never** modifies content outside the `DYNAMIC-METRICS` markers.

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Single platform API fails | Preserves previous data for that platform, marks as "stale" |
| All platforms fail | Preserves entire previous metrics file, does not commit |
| API rate limited | Logs warning, preserves previous data |
| Network timeout | 15-second timeout per request, graceful error |
| Invalid response | Logs error, preserves previous valid data |
| Partial success | Updates successful platforms, preserves stale data for failed ones |

## Data Sources

| Platform | API Type | Auth Required | Data Retrieved |
|----------|----------|---------------|----------------|
| **GitHub** | REST API v3 | Optional (GITHUB_TOKEN increases rate limit) | Repos, stars, followers, languages |
| **LeetCode** | GraphQL (public) | None | Problems solved, difficulty breakdown, ranking |
| **TryHackMe** | REST (public) | Optional (THM_API_KEY) | Rank, rooms completed, badges, points |
| **Hack The Box** | REST (public/auth) | Optional (HTB_API_KEY) | Rank, points, machine owns |

## Required GitHub Secrets

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto-provided | GitHub API access (automatic in Actions) |
| `THM_API_KEY` | Optional | TryHackMe authenticated API access |
| `HTB_API_KEY` | Optional | Hack The Box authenticated API access |

## Security Considerations

1. **No secrets in code:** All credentials use GitHub Actions Secrets or environment variables
2. **No secrets in JSON:** `profile-metrics.json` contains only public data
3. **Minimal permissions:** Workflow uses `contents: write` only
4. **No arbitrary execution:** Scripts use only `urllib` (stdlib) — no shell commands
5. **Input validation:** All API responses are validated before use
6. **Rate limit awareness:** Respects API rate limits, uses graceful fallback
7. **Token masking:** GITHUB_TOKEN is automatically masked in Actions logs

## Adding New Platforms

1. Create `scripts/fetch_<platform>.py` following the existing pattern
2. Import and call it in `scripts/update_metrics.py`
3. Add any required secrets to `.github/workflows/update-profile.yml`
4. Update `generate_dynamic_section()` to include the new data

## Local Development

```bash
# Set environment variables
export GITHUB_USERNAME=Riteshkumar1205
export LEETCODE_USERNAME=RiteshKumar2512
export THM_USERNAME=RITESH26
export HTB_USERNAME=Hackglb2025

# Run the update
python scripts/update_metrics.py
```

## Where to Update Content

| Content Type | File | Section |
|-------------|------|---------|
| Projects | `README.md` | Featured Projects section |
| Certifications | `README.md` | Certifications table |
| Experience | `README.md` | Experience section |
| Tech stack | `README.md` | Technical Capability Matrix |
| Automation config | `.github/workflows/update-profile.yml` | Environment variables |
| Platform usernames | `scripts/update_metrics.py` | Default values in `main()` |

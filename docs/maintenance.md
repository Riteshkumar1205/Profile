# Maintenance Guide

This document outlines how to maintain, debug, and expand the profile repository.

## Adding a New Project to the README

1. Open `README.md`.
2. Locate the `## 🧾 Proof of Work Layer` or `## 🏗️ Architecture Gallery`.
3. Add the new project ensuring you do **not** write inside the `<!-- DYNAMIC-RECENT:START -->` or `<!-- DYNAMIC-METRICS:START -->` markers.
4. Push to `main`. The `validate-profile.yml` workflow will automatically check that any URLs you added are valid.

## Debugging Workflow Failures

If the `update-profile.yml` workflow fails:
1. Go to the **Actions** tab on GitHub.
2. Select the failed workflow run.
3. Check the step output for `python scripts/update_metrics.py`.
4. The orchestrator is failure-tolerant; it will try to preserve past JSON state if APIs go down. If it fails entirely, check your GitHub secrets or ensure your GitHub token isn't expired.

## Extending the Dashboard Generator

The `scripts/generate_dashboard.py` currently fetches the 4 most recently updated repositories.
- To increase this number, edit line `recent = original_repos[:4]` in `scripts/generate_dashboard.py`.
- To exclude a repository from the list, modify the list comprehension logic in `generate_recently_built()`.

## Assets and Diagrams

The repository uses `mermaid` extensively to generate reliable, GitHub-native architectural diagrams (e.g. for `LabAgent` and `DLP Intelligence`).
- If you wish to use standalone SVGs in the future, save them in `assets/architecture/`.
- Ensure SVGs are optimized and stripped of inline javascript to avoid sanitization by GitHub's rendering engine.

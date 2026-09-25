# Profile Repository Architecture

This document outlines the architecture and workflows that power the `Riteshkumar1205/Riteshkumar1205` GitHub Profile Repository.

## Repository Layout

```
Riteshkumar1205/
│
├── README.md                      ← The main entrypoint containing the generated profile
│
├── requirements.txt               ← Global Python dependencies
│
├── .github/
│   └── workflows/
│       ├── update-profile.yml     ← Daily scheduled workflow to update metrics/dashboard
│       └── validate-profile.yml   ← CI/CD pipeline triggered on pushes and pull requests
│
├── scripts/                       ← Python automation scripts
│   ├── update_metrics.py          ← Entrypoint for the metrics data update
│   ├── fetch_github.py            
│   ├── fetch_leetcode.py          
│   ├── fetch_tryhackme.py         
│   ├── fetch_htb.py               
│   ├── generate_dashboard.py      ← Generates the 'Recently Built' section
│   ├── generate_architecture.py   ← (Reserved for future architecture auto-generation)
│   └── validate_links.py          ← Validation script that checks URLs in the README
│
├── data/                          ← Structured data storage (JSON)
│   ├── profile-metrics.json       
│   ├── projects.json              
│   └── activity.json              
│
├── assets/                        ← Static assets and generated graphics
│   ├── 360-security-profile.svg   
│   ├── architecture/              
│   └── generated/                 
│
└── docs/                          ← Documentation
    ├── automation.md              
    ├── architecture.md            
    └── maintenance.md             
```

## Workflows

1. **Update Metrics (`update-profile.yml`)**
   - Fetches data from 4 APIs (GitHub, LeetCode, TryHackMe, HTB).
   - Generates the 'Recently Built' dynamic section.
   - Pushes changes back to the repository if any differences are detected.

2. **Validate Profile (`validate-profile.yml`)**
   - Syntax-checks all Python files.
   - Validates all internal JSON data files.
   - Verifies the `DYNAMIC` markers exist in the `README.md`.
   - Checks that all URLs in the README return 200 OK statuses.

## Content Management

The README uses a hybrid content management approach:
- **Human Content**: The top section, quick view, capability maps, timeline, architecture blocks, and contact info are manually authored.
- **Dynamic Content**: Sections wrapped in `<!-- DYNAMIC-METRICS:START -->` and `<!-- DYNAMIC-RECENT:START -->` are automatically rewritten by the Python scripts via GitHub Actions.

import re
import sys
import logging
import urllib.request
from urllib.error import URLError, HTTPError
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("validate_links")

REPO_ROOT = Path(__file__).parent.parent
README_FILE = REPO_ROOT / "README.md"

def extract_links(text):
    # Matches http(s):// urls and stops at standard markdown boundary characters.
    pattern = r'http[s]?://[^\s)\]"\']+'
    return re.findall(pattern, text)

def validate_links():
    if not README_FILE.exists():
        logger.error("README.md not found.")
        sys.exit(1)
        
    content = README_FILE.read_text(encoding="utf-8")
    links = set(extract_links(content))
    
    # Remove markdown closing parenthesis if accidentally matched
    cleaned_links = set()
    for link in links:
        if link.endswith(')'):
            link = link[:-1]
        cleaned_links.add(link)
        
    logger.info(f"Found {len(cleaned_links)} unique links. Validating...")
    
    errors = 0
    for link in cleaned_links:
        # Ignore dummy/shield links for speed, or we can check them too.
        if "img.shields.io" in link or "github-readme-stats" in link or "github-readme-streak-stats" in link:
            continue
            
        try:
            req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status >= 400:
                    logger.error(f"Broken link: {link} (Status {response.status})")
                    errors += 1
        except HTTPError as e:
            # Some sites block python user agents with 403, we can ignore 403s as false positives
            if e.code == 403:
                logger.warning(f"Forbidden (403) for link: {link}. May be valid but blocked.")
            elif e.code == 429:
                logger.warning(f"Rate limited (429) for link: {link}.")
            else:
                logger.error(f"Broken link: {link} (HTTP {e.code})")
                errors += 1
        except URLError as e:
            logger.error(f"Failed to reach link: {link} ({e.reason})")
            errors += 1
        except Exception as e:
            logger.error(f"Error checking link: {link} ({str(e)})")
            errors += 1

    if errors > 0:
        logger.error(f"Validation failed with {errors} broken links.")
        sys.exit(1)
    else:
        logger.info("All links validated successfully!")

if __name__ == "__main__":
    validate_links()

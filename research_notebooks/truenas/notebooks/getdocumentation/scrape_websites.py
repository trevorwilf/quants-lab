import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from scrapling.fetchers import StealthyFetcher

# Enable adaptive mode (recommended for long-term scraping)
StealthyFetcher.adaptive = True

MEXC_DOCS_BASE = "https://www.mexc.com/api-docs/spot-v3"
MEXC_DOCS_PREFIX = "/api-docs/spot-v3"


def ensure_folder(site_name: str) -> Path:
    folder = Path(f"./webscrape/{site_name}")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def slugify(url: str) -> str:
    """Turn a MEXC docs URL into a safe filename."""
    path = urlparse(url).path                       # /api-docs/spot-v3/some-page
    tail = path.replace(MEXC_DOCS_PREFIX, "")       # /some-page
    tail = tail.strip("/") or "index"               # some-page  (or "index" for root)
    return "mexc_spot_" + re.sub(r"[^a-zA-Z0-9]+", "_", tail)


# ==================== Fetch a page with StealthyFetcher ====================
def fetch_page(url: str, **kwargs):
    """Return a Scrapling page object or None."""
    defaults = dict(
        headless=True,
        network_idle=True,
        solve_cloudflare=True,
        humanize=True,
    )
    defaults.update(kwargs)
    try:
        return StealthyFetcher.fetch(url, **defaults)
    except Exception as e:
        print(f"   ❌ Fetch failed {url}: {e}")
        return None


def get_html(page) -> str:
    if hasattr(page, "html_content"):
        return page.html_content
    return page.body.decode("utf-8", errors="ignore")


# ==================== Discover all spot-v3 doc links ====================
def discover_mexc_spot_v3_links() -> list[str]:
    """
    Load the MEXC docs introduction page (or the sidebar/navigation),
    extract every link whose path starts with /api-docs/spot-v3/,
    and return a deduplicated, sorted list of absolute URLs.
    """
    seed_url = f"{MEXC_DOCS_BASE}/introduction"
    print(f"🔍 Discovering pages from {seed_url} …")

    page = fetch_page(seed_url)
    if page is None:
        print("   ⚠️  Could not load seed page – falling back to manual list")
        return []

    html = get_html(page)

    # --- Strategy 1: pull hrefs from <a> tags via Scrapling selectors ---
    found: set[str] = set()
    try:
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
            if href.startswith(MEXC_DOCS_PREFIX):
                found.add(urljoin("https://www.mexc.com", href))
            elif href.startswith("http") and MEXC_DOCS_PREFIX in href:
                found.add(href.split("?")[0].split("#")[0])
    except Exception:
        pass

    # --- Strategy 2: regex over raw HTML (catches JS-rendered hrefs) ---
    for match in re.finditer(r'["\'](\/api-docs\/spot-v3\/[^"\'#?]+)', html):
        found.add(urljoin("https://www.mexc.com", match.group(1)))
    for match in re.finditer(
        r'["\'](https?://www\.mexc\.com/api-docs/spot-v3/[^"\'#?]+)', html
    ):
        found.add(match.group(1))

    # Always include the root / introduction just in case
    found.add(f"{MEXC_DOCS_BASE}/introduction")

    urls = sorted(found)
    print(f"   📋 Found {len(urls)} unique spot-v3 doc page(s)\n")
    for u in urls:
        print(f"      • {u}")
    print()
    return urls


# ==================== Scrape & save an HTML page ====================
def scrape_html(url: str, site_name: str, filename: str):
    print(f"🌐 Scraping HTML: {url}")
    page = fetch_page(url)
    if page is None:
        return False

    html_content = get_html(page)
    save_path = ensure_folder(site_name) / f"{filename}.html"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"   ✅ Saved → {filename}.html ({len(html_content):,} chars)")
    return True


# ==================== Scrape JSON APIs ====================
def scrape_json(url: str, site_name: str, filename: str):
    print(f"📡 Fetching JSON: {url}")
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/134.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        save_path = ensure_folder(site_name) / f"{filename}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Saved → {filename}.json")
        return True
    except Exception as e:
        print(f"   ❌ JSON error {url}: {e}")
    return False


# ====================== RUN THE SCRAPE ======================
if __name__ == "__main__":
    print("🚀 Starting full scrape…\n")

    # ---------- MEXC: auto-discover & crawl all spot-v3 pages ----------
    print("=== MEXC (auto-discover) ===")
    doc_urls = discover_mexc_spot_v3_links()

    if not doc_urls:
        # Fallback: hard-coded list so the script still does *something*
        print("   ⚠️  Using fallback list")
        doc_urls = [
            f"{MEXC_DOCS_BASE}/introduction",
            f"{MEXC_DOCS_BASE}/websocket-market-streams",
            f"{MEXC_DOCS_BASE}/market-data-endpoints",
            f"{MEXC_DOCS_BASE}/spot-account-trade",
            f"{MEXC_DOCS_BASE}/wallet-endpoints",
            f"{MEXC_DOCS_BASE}/sub-account-endpoints",
            f"{MEXC_DOCS_BASE}/websocket-account-streams",
            f"{MEXC_DOCS_BASE}/rebate-endpoints",
            f"{MEXC_DOCS_BASE}/other-endpoints",
        ]

    for url in doc_urls:
        filename = slugify(url)
        scrape_html(url, "mexc", filename)

    # Sample JSON endpoints
    print("\n--- MEXC sample API data ---")
    scrape_json(
        "https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT",
        "mexc",
        "mexc_btcusdt_ticker",
    )
    scrape_json(
        "https://api.mexc.com/api/v3/ticker/bookTicker?symbol=BTCUSDT",
        "mexc",
        "mexc_btcusdt_bookticker",
    )

    # ---------- NonKYC ----------
    print("\n=== NonKYC ===")
    nonkyc_docs = [
        ("https://nonkyc.io/wsapi", "nonkyc_wsapi"),
        ("https://nonkyc.io/", "nonkyc_home"),
        ("https://api.nonkyc.io/", "nonkyc_api_root"),
    ]
    for url, name in nonkyc_docs:
        scrape_html(url, "nonkyc", name)

    scrape_json(
        "https://api.nonkyc.io/api/v2/public/ticker", "nonkyc", "nonkyc_all_tickers"
    )
    scrape_json(
        "https://api.nonkyc.io/api/v2/public/markets", "nonkyc", "nonkyc_markets"
    )

    print("\n🎉 DONE! Everything is saved in ./webscrape/")
    print("   • mexc/   → All spot-v3 API doc pages + sample JSON")
    print("   • nonkyc/ → WSAPI docs + sample market JSON")
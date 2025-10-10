#!/usr/bin/env python3
"""
tor_crawler.py

Simple Tor-backed crawler using Selenium+Firefox (geckodriver).
- Reads a newline-separated file of URLs (can include .onion addresses)
- Deduplicates and crawls up to max_links_per_site links
- Searches page source for a keyword
- Writes simple results.html with matches (link, title, snippet, timestamp)

USAGE (example):
    python3 tor_crawler.py --input input_links.txt --keyword test --max 20 --headless

LEGAL: Use only for authorized/legitimate research. Do NOT use to access illegal content.
"""

import argparse
import time
import random
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup

# === Configuration defaults ===
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
GECKODRIVER_PATH = "/usr/local/bin/geckodriver"  # change if needed
FIREFOX_BINARY = None  # set to path if nonstandard, else None

# === Helper functions ===
def make_firefox_driver(headless=True, tor_host=TOR_SOCKS_HOST, tor_port=TOR_SOCKS_PORT):
    """Create a Firefox Selenium WebDriver configured to use Tor SOCKS proxy."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    # If you installed a custom firefox binary:
    if FIREFOX_BINARY:
        options.binary_location = FIREFOX_BINARY

    # Create a Firefox profile and configure Tor SOCKS proxy
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", tor_host)
    profile.set_preference("network.proxy.socks_port", tor_port)
    profile.set_preference("network.proxy.socks_remote_dns", True)
    profile.set_preference("webdriver_assume_untrusted_issuer", False)
    profile.update_preferences()

    # Attach the profile properly for Selenium 4.6+
    options.profile = profile

    # Start the Firefox WebDriver
    service = Service(GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)

    driver.set_page_load_timeout(60)  # Tor can be slow
    return driver


def search_in_html(html, keyword):
    """Return a short snippet around the first occurrence of keyword in html (case-insensitive) or None."""
    if not keyword:
        return None
    lowered = html.lower()
    k = keyword.lower()
    idx = lowered.find(k)
    if idx == -1:
        return None
    start = max(0, idx - 120)
    end = min(len(html), idx + 120)
    snippet = html[start:end]
    # Clean snippet with BeautifulSoup to remove tags if present
    try:
        s = BeautifulSoup(snippet, "lxml").get_text()
    except Exception:
        s = snippet
    return "..." + s.strip().replace("\n", " ") + "..."

def write_result_html(entries, outpath="results.html"):
    """Write results list to a simple HTML file."""
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("<!doctype html>\n<html><head><meta charset='utf-8'><title>Crawl Results</title></head><body>\n")
        f.write(f"<h1>Crawl Results — {datetime.utcnow().isoformat()} UTC</h1>\n")
        for e in entries:
            f.write("<div style='margin-bottom:1.2em;padding:8px;border:1px solid #ddd;'>\n")
            f.write(f"<a href='{e['url']}' target='_blank'>{e['url']}</a><br/>\n")
            f.write(f"<strong>Title:</strong> {e.get('title','(no title)')}<br/>\n")
            f.write(f"<strong>Found:</strong> {e.get('snippet','')}<br/>\n")
            f.write(f"<strong>When:</strong> {e.get('timestamp')}<br/>\n")
            f.write("</div>\n")
        f.write("</body></html>\n")

# === Main crawler ===
def crawl_file(input_path, keyword, max_links_per_site=50, delay_min=5, delay_max=12, headless=True):
    # read links
    with open(input_path, "r", encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    links = [ln.strip() for ln in raw if ln.strip()]
    if not links:
        print("No links found in the input file.", file=sys.stderr)
        return

    # deduplicate preserving order
    seen = set()
    uniq_links = []
    for l in links:
        if l not in seen:
            seen.add(l)
            uniq_links.append(l)

    print(f"Total unique links to consider: {len(uniq_links)}")
    # limit total overall? we follow per-site limit only (as in screenshot)
    entries = []
    driver = None
    try:
        driver = make_firefox_driver(headless=headless)
    except WebDriverException as e:
        print("Failed to start geckodriver/firefox. Ensure geckodriver path is correct and Firefox is installed.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return

    count = 0
    try:
        for link in uniq_links:
            # stop if we reached per-site cap (this mimics screenshot logic where count resets per file)
            count += 1
            if count > max_links_per_site:
                print("Reached max_links_per_site limit, stopping.")
                break

            print(f"\n[{count}] Crawling: {link}")
            try:
                # Try to navigate. Tor can make sites slow/unreliable, so catch timeouts
                driver.get(link)
                time.sleep(1)  # small wait for initial render

                # Get page source
                html = driver.page_source or ""
                # try to get title
                try:
                    title = driver.title
                except Exception:
                    title = ""

                snippet = search_in_html(html, keyword) if keyword else None
                if snippet:
                    entry = {
                        "url": link,
                        "title": title,
                        "snippet": snippet,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    entries.append(entry)
                    print(f"  -> MATCH: keyword found, saved result for {link}")
                else:
                    print("  -> no keyword match")

            except TimeoutException:
                print(f"  -> Timeout loading {link}")
            except WebDriverException as e:
                print(f"  -> WebDriver error for {link}: {e}")
            except Exception as e:
                print(f"  -> Error while crawling {link}: {e}")

            # polite random delay between requests (important when crawling)
            delay = random.uniform(delay_min, delay_max)
            print(f"  sleeping {delay:.1f}s")
            time.sleep(delay)

    finally:
        if driver:
            driver.quit()

    # write results
    timestamped = f"results_{int(time.time())}.html"
    write_result_html(entries, outpath=timestamped)
    print(f"\nWrote {len(entries)} matches to {timestamped}")

# === CLI ===
def parse_args():
    p = argparse.ArgumentParser(description="Tor-backed crawler (Selenium + Firefox).")
    p.add_argument("--input", "-i", default="input_links.txt", help="Input file with newline-separated URLs")
    p.add_argument("--keyword", "-k", default="", help="Keyword to search for (case-insensitive)")
    p.add_argument("--max", "-m", type=int, default=50, help="Max links to crawl (per file)")
    p.add_argument("--headless", action="store_true", help="Run Firefox headless")
    p.add_argument("--delay-min", type=float, default=5.0, help="Minimum delay between requests (sec)")
    p.add_argument("--delay-max", type=float, default=12.0, help="Maximum delay between requests (sec)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # Safety check
    if not args.keyword:
        print("Warning: no keyword provided — script will crawl but won't record keyword matches.", file=sys.stderr)
    print(f"Starting crawl (input={args.input}, keyword={args.keyword!r}, max={args.max})")
    crawl_file(args.input, args.keyword, max_links_per_site=args.max, delay_min=args.delay_min, delay_max=args.delay_max, headless=args.headless)

import argparse
import json
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session(user_agent: str):
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    })

    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=1.2,                 # exponential backoff
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,    # honor Retry-After if present
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def polite_sleep(base_delay: float, jitter: float = 0.6):
    # sleep ~ base_delay ± jitter
    time.sleep(max(0.0, base_delay + random.uniform(-jitter, jitter)))


from bs4 import BeautifulSoup

def crawl_by_selector(
    session: requests.Session,
    url: str,
    selector: str,
    timeout: int = 20,
    base_delay: float = 1.0,   # 1 request/sec baseline
) -> dict:
    resp = session.get(url, timeout=timeout)

    # If still 429 after urllib3 retry, throttle harder
    if resp.status_code == 429:
        # sleep a bit more and raise (caller can retry or log)
        polite_sleep(base_delay * 6)
        resp.raise_for_status()

    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    node = soup.select_one(selector)
    if node is None:
        raise ValueError(f"Selector not found: {selector}")

    for tag in node(["script", "style", "noscript"]):
        tag.decompose()

    text = "\n".join(
        line.strip()
        for line in node.get_text(separator="\n").splitlines()
        if line.strip()
    )
    title = soup.title.text.strip() if soup.title else ""

    # polite pacing every successful request
    polite_sleep(base_delay)

    return {"url": url, "title": title, "text": text}


def read_urls(url: Optional[str], url_file: Optional[str]) -> list[str]:
    if url:
        return [url.strip()]

    if not url_file:
        raise ValueError("Provide either --url or --url-file")

    urls: list[str] = []
    with open(url_file, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            urls.append(s)
    if not urls:
        raise ValueError("No URLs found in --url-file")
    return urls


def parse_args():
    p = argparse.ArgumentParser("Crawl page content by CSS selector")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="Single URL to crawl")
    g.add_argument("--url-file", help="Text file containing URLs (one per line)")

    p.add_argument(
        "--selector",
        default="#divContentDoc > div.content1",
        help="CSS selector to extract content",
    )
    p.add_argument("--timeout", type=int, default=15, help="Request timeout (seconds)")
    p.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (compatible; CrankyCrawler/1.0)",
        help="Custom User-Agent",
    )

    p.add_argument(
        "--out",
        default="",
        help="Output path. If endswith .jsonl -> write JSONL. Else write a single JSON (only valid for --url).",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first error (default: continue and report errors)",
    )
    p.add_argument("--delay", type=float, default=1.2, help="Delay between requests (seconds)")
    return p.parse_args()


def main():
    args = parse_args()
    urls = read_urls(args.url, args.url_file)

    results: list[dict] = []
    errors: list[dict] = []

    out_path = args.out.strip()
    write_jsonl = bool(out_path) and out_path.lower().endswith(".jsonl")

    jsonl_f = None
    if out_path and write_jsonl:
        jsonl_f = open(out_path, "w", encoding="utf-8")

    try:
        session = make_session("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")

        for u in tqdm(urls, desc="Crawling", unit="url"):
            try:
                item = crawl_by_selector(
                    session=session,
                    url=u,
                    selector=args.selector,
                    timeout=args.timeout,
                    base_delay=args.delay,
                )

                if jsonl_f is not None:
                    jsonl_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                else:
                    results.append(item)

            except Exception as e:
                err = {"url": u, "error": str(e)}
                errors.append(err)
                if args.fail_fast:
                    raise

        if out_path and not write_jsonl:
            if len(results) != 1 and args.url_file:
                raise ValueError(
                    "Writing a single JSON file only supports --url. "
                    "Use --out something.jsonl for multiple URLs."
                )
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results[0] if results else {}, f, ensure_ascii=False, indent=2)

        if not out_path:
            if len(results) == 1:
                print(json.dumps(results[0], ensure_ascii=False, indent=2))
            else:
                for item in results:
                    print(json.dumps(item, ensure_ascii=False))

        if errors:
            print(f"\n[WARN] {len(errors)} URL(s) failed:", file=sys.stderr)
            for e in errors[:10]:
                print(f"- {e['url']}: {e['error']}", file=sys.stderr)
            if len(errors) > 10:
                print(f"... and {len(errors)-10} more", file=sys.stderr)

    finally:
        if jsonl_f is not None:
            jsonl_f.close()


if __name__ == "__main__":
    main()
